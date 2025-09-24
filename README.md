# Generador de README para GitHub a partir de CV en PDF

Este proyecto genera un archivo `README.md` para tu perfil de GitHub, extrayendo datos de tu Curriculum Vitae en PDF.

## ¿Cómo funciona?

1. Ejecuta el servidor Flask en tu máquina local.
2. Accede a la web local.
3. Sube tu CV en PDF.
4. Descarga el README.md ya generado y listo para personalizar.

## Privacidad

- El archivo PDF se procesa solo localmente.
- No se almacena ni se envía a servidores externos.
- El README generado puede contener datos personales: revisa y edita antes de subirlo a GitHub.

## Instalación rápida

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Luego accede a `http://localhost:5000` en tu navegador.

## Personalización

- Edita la plantilla `example_README.md` para adaptarla a tu estilo y datos.
- La extracción automática del CV se puede mejorar integrando librerías como `pdfplumber`.

---

¿Dudas, sugerencias? ¡Crea un issue!