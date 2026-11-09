"""Uzliek "SBE projekti" saīsni uz darbvirsmas (Windows) ar savu ikonu.

Lietošana:  python bot/app_saisne.py
Ikona: bot/sablons/arhivs/sbe.ico (uzzīmē šeit ar Pillow, ja tās vēl nav vai ar --ikona).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ICO = os.path.join(HERE, 'sablons', 'arhivs', 'sbe.ico')


def draw_icon(path):
    from PIL import Image, ImageDraw
    S = 1024
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([40, 40, S - 40, S - 40], radius=190, fill=(42, 46, 51, 255))
    w = 46
    # mājas siluets ar 45° jumtu un logu: tās pašas kontūras kā redaktora ikonām
    roof = [(230, 520), (512, 250), (794, 520)]
    d.line(roof, fill=(91, 155, 248, 255), width=w, joint='curve')
    for x, y in (roof[0], roof[2]):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=(91, 155, 248, 255))
    d.line([(300, 470), (300, 790), (724, 790), (724, 470)], fill=(230, 233, 236, 255), width=w, joint='curve')
    d.rectangle([440, 560, 584, 680], outline=(230, 233, 236, 255), width=34)
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    im.save(path, sizes=sizes)


def desktop():
    try:
        return subprocess.run(['powershell', '-NoProfile', '-Command', "[Environment]::GetFolderPath('Desktop')"],
                              capture_output=True, text=True).stdout.strip() or os.path.join(os.path.expanduser('~'), 'Desktop')
    except Exception:
        return os.path.join(os.path.expanduser('~'), 'Desktop')


def main():
    if '--ikona' in sys.argv or not os.path.exists(ICO):
        draw_icon(ICO)
    pyw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    if not os.path.exists(pyw):
        pyw = sys.executable
    lnk = os.path.join(desktop(), 'SBE projekti.lnk')
    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:SBE_LNK);"
          "$s.TargetPath=$env:SBE_PY;$s.Arguments='\"'+$env:SBE_APP+'\"';$s.WorkingDirectory=$env:SBE_DIR;"
          "$s.IconLocation=$env:SBE_ICO+',0';$s.Description='SBE projektu arhīvs un rasējuma redaktors';$s.Save()")
    env = dict(os.environ, SBE_LNK=lnk, SBE_PY=pyw, SBE_APP=os.path.join(HERE, 'app.py'), SBE_DIR=HERE, SBE_ICO=ICO)
    subprocess.run(['powershell', '-NoProfile', '-Command', ps], check=True, env=env)
    print(lnk)


if __name__ == '__main__':
    main()
