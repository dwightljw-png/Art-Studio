from pathlib import Path

html_path = Path("app/src/main/assets/art_studio_android.html")
html = html_path.read_text(encoding="utf-8")

required = [
    "ART STUDIO v4.0.8",
    'id="fullscreenBtn"',
    'id="saveBtn"',
    'id="exportBtn"',
    'id="printBtn"',
    'id="imageInput"',
    'id="projectInput"',
    "function download(blob,name)",
    "window.print()",
    "printRoot",
]
for token in required:
    if token not in html:
        raise SystemExit(f"Required HTML token missing: {token}")

# Keep the actual button in the DOM so the original fullscreen JS can attach.
# Suppress only its visual presence, plus the divider directly after it.
html = html.replace("</head>", """
<style id="androidStudioPatch">
#fullscreenBtn, #fullscreenBtn + .divider { display: none !important; }
</style>
</head>""", 1)

original_download = """function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000)}"""
patched_download = """function download(blob,name){
 if(window.AndroidApp&&typeof AndroidApp.saveBase64File==='function'){
  const reader=new FileReader();
  reader.onload=()=>AndroidApp.saveBase64File(String(reader.result),String(name||'art-studio-export'));
  reader.onerror=()=>toast('안드로이드 파일 저장 준비에 실패했습니다');
  reader.readAsDataURL(blob);
  return;
 }
 const url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(url),60000)
}"""
if html.count(original_download) != 1:
    raise SystemExit("Could not find unique download function to bridge Android save")
html = html.replace(original_download, patched_download, 1)

# The HTML already selects A4 portrait/landscape based on the canvas.
# Pass that exact orientation to the Android bridge; do not reflow or rotate artwork.
native_print_call = "try{window.print()}catch"
if html.count(native_print_call) != 1:
    raise SystemExit("Could not find unique print invocation to forward orientation")
html = html.replace(native_print_call, "try{window.print(orientation)}catch", 1)

# The app prepares #printRoot and its A4 image before calling window.print().
# Preserve all those preparations and redirect just the print invocation.
bridge = """
<script id="androidStudioNativeBridge">
(function(){
 if(!(window.AndroidApp&&typeof AndroidApp.printWebView==='function'))return;
 window.print=function(orientation){
   AndroidApp.printWebView('ART STUDIO A4', orientation==='landscape');
 };
})();
</script>
"""
html = html.replace("</body>", bridge + "\n</body>", 1)
html_path.write_text(html, encoding="utf-8")
print("Patched ART STUDIO for Android:", html_path.stat().st_size)
