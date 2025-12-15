# Documentación de gee_acolite

Esta carpeta contiene la documentación de gee_acolite generada con Sphinx.

## Estructura

```
sphinx/
├── source/           # Archivos fuente RST
│   ├── modules/      # Documentación de módulos
│   ├── user_guide/   # Guías de usuario
│   ├── examples/     # Ejemplos de uso
│   └── conf.py       # Configuración de Sphinx
├── build/            # Documentación generada
│   └── html/         # HTML generado
├── Makefile          # Makefile para Linux/Mac
└── make.bat          # Script para Windows
```

## Generar la documentación

### En Windows:

```bash
cd sphinx
.\make.bat html
```

### En Linux/Mac:

```bash
cd sphinx
make html
```

La documentación generada estará en `build/html/index.html`.

## Instalar dependencias

```bash
pip install -r ../docs/requirements.txt
```

## Ver la documentación localmente

Después de generar, puedes abrir `build/html/index.html` en tu navegador o usar un servidor local:

```bash
cd build/html
python -m http.server 8000
```

Luego visita http://localhost:8000

## Actualizar la documentación

1. Edita los archivos `.rst` en `source/`
2. Regenera con `make html` o `.\make.bat html`
3. Revisa los cambios en `build/html/`

## Publicar en GitHub Pages

La documentación se publica automáticamente en GitHub Pages mediante GitHub Actions cuando se hace push a la rama `docs`.
