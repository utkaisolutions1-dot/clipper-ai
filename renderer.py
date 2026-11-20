import os
import subprocess
import cv2


def detect_face_fallback(video_path: str):
    """Respaldo local con OpenCV si no se pasaron coordenadas desde Gemini."""
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    sample_step = max(1, total_frames // 20)

    detections = []
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_step == 0 and orig_w > 0 and orig_h > 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                cx = (x + w / 2.0) / orig_w
                cy = (y + h / 2.0) / orig_h
                detections.append((cx, cy, w / orig_w))
        frame_idx += 1

    cap.release()
    if not detections:
        return False, 0.5, 0.5

    avg_cx = sum(d[0] for d in detections) / len(detections)
    avg_cy = sum(d[1] for d in detections) / len(detections)
    avg_ratio = sum(d[2] for d in detections) / len(detections)
    return (avg_ratio < 0.18), avg_cx, avg_cy


def _build_pip_filter(cam_x: int, cam_y: int, cam_w: int, cam_h: int, orig_w: int, orig_h: int, ass_escaped: str) -> str:
    """
    Construye la composición Picture-in-Picture (1080x1920):
    - Fondo superior desenfocado (1080x620) con los colores de la cámara.
    - Gameplay abajo (1080x1320) desde y=600 hasta y=1920.
    - Tarjeta cuadrada del streamer (560x560) con esquinas redondeadas (r=32) flotando en x=260, y=130.
    """
    game_w = min(orig_w, int(orig_h * (1080 / 1320)))
    game_x = int((orig_w - game_w) / 2)

    # Fórmula alfa en FFmpeg para redondear las 4 esquinas de un cuadro de 560x560 con radio 32px
    r = 32
    alpha_expr = (
        f"if(lt(X,{r})*lt(Y,{r}), if(lte(hypot({r}-X,{r}-Y),{r}),255,0), "
        f"if(gt(X,W-{r})*lt(Y,{r}), if(lte(hypot(X-(W-{r}),{r}-Y),{r}),255,0), "
        f"if(lt(X,{r})*gt(Y,H-{r}), if(lte(hypot({r}-X,Y-(H-{r})),{r}),255,0), "
        f"if(gt(X,W-{r})*gt(Y,H-{r}), if(lte(hypot(X-(W-{r}),Y-(H-{r})),{r}),255,0), 255))))"
    )

    return (
        # 1. Extraer la región de la cámara y duplicarla en 2 flujos
        f"[0:v]crop={cam_w}:{cam_h}:{cam_x}:{cam_y},split=2[cam_bg_src][cam_fg_src];"
        # 2. Fondo superior desenfocado (1080x620)
        f"[cam_bg_src]scale=1080:620:force_original_aspect_ratio=increase,crop=1080:620,gblur=sigma=35[top_bg];"
        # 3. Gameplay inferior (1080x1320)
        f"[0:v]crop={game_w}:{orig_h}:{game_x}:0,scale=1080:1320[bottom_game];"
        # 4. Unir fondo superior y gameplay (1080x1920 base, solapando 20px en y=600)
        f"color=c=black:s=1080x1920[canvas];"
        f"[canvas][top_bg]overlay=0:0[base1];"
        f"[base1][bottom_game]overlay=0:600[base2];"
        # 5. Tarjeta flotante cuadrada (560x560) con esquinas redondeadas
        f"[cam_fg_src]scale=560:560:force_original_aspect_ratio=increase,crop=560:560,format=yuva420p,"
        f"geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='{alpha_expr}'[cam_card];"
        # 6. Superponer tarjeta en el centro superior (x=260, y=130) y quemar subtítulos
        f"[base2][cam_card]overlay=260:130:shortest=1,ass='{ass_escaped}'[out]"
    )


def render_vertical_clip(raw_clip_path: str, ass_path: str, final_output_path: str, facecam=None):
    cap = cv2.VideoCapture(raw_clip_path)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")

    # 1. Usar coordenadas fijas de la facecam detectada por Gemini
    if facecam is not None and getattr(facecam, "has_facecam", False):
        x1 = int(max(0.0, min(1.0, facecam.x_min)) * orig_w)
        y1 = int(max(0.0, min(1.0, facecam.y_min)) * orig_h)
        x2 = int(max(0.0, min(1.0, facecam.x_max)) * orig_w)
        y2 = int(max(0.0, min(1.0, facecam.y_max)) * orig_h)

        # Hacer el recorte cuadrado centrado sobre la caja detectada para que no recorte ni deforme
        box_w = max(120, x2 - x1)
        box_h = max(120, y2 - y1)
        side = min(orig_w, orig_h, max(box_w, box_h))
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        cam_x = max(0, min(orig_w - side, cx - side // 2))
        cam_y = max(0, min(orig_h - side, cy - side // 2))

        filter_complex = _build_pip_filter(cam_x, cam_y, side, side, orig_w, orig_h, ass_escaped)

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", raw_clip_path,
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-map", "0:a",
                "-c:v", "libx264", "-preset", "fast", "-crf", "21",
                "-c:a", "copy",
                final_output_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return

    # 2. Respaldo automático con OpenCV si no venían coordenadas
    is_gaming, cx_norm, cy_norm = detect_face_fallback(raw_clip_path)

    if is_gaming:
        side = min(orig_w, orig_h, int(orig_w * 0.25))
        cam_x = max(0, min(orig_w - side, int(cx_norm * orig_w - side // 2)))
        cam_y = max(0, min(orig_h - side, int(cy_norm * orig_h - side // 2)))

        filter_complex = _build_pip_filter(cam_x, cam_y, side, side, orig_w, orig_h, ass_escaped)

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", raw_clip_path,
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-map", "0:a",
                "-c:v", "libx264", "-preset", "fast", "-crf", "21",
                "-c:a", "copy",
                final_output_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    else:
        # Modo Podcast / Charla en pantalla completa vertical
        crop_w = min(orig_w, int(orig_h * 9 / 16))
        crop_x = max(0, min(orig_w - crop_w, int((cx_norm * orig_w) - (crop_w / 2))))
        vf_filter = f"crop={crop_w}:{orig_h}:{crop_x}:0,scale=1080:1920,ass='{ass_escaped}'"

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", raw_clip_path,
                "-vf", vf_filter,
                "-c:v", "libx264", "-preset", "fast", "-crf", "21",
                "-c:a", "copy",
                final_output_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )