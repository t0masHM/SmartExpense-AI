# CAPTON

Plataforma web **on-premise** para digitalizar comprobantes, extraer campos contables chilenos (RUT, fechas, montos, folio) y **reconstruir zonas dañadas** de la imagen con visión computacional + un clasificador de caracteres. Todo corre en Docker: los datos financieros no salen de la máquina.

## Qué resuelve

Los departamentos contables pierden horas digitando boletas y facturas, y fallan cuando el papel está borroso, manchado o incompleto. CAPTON:

1. Recibe la foto del comprobante.
2. Detecta daño (manchas, brillos, arrugas, márgenes rasgados) y restaura píxeles con inpainting.
3. Corre OCR (Tesseract spa+eng) y repara caracteres de baja confianza con un modelo **HOG + Random Forest** entrenado de forma sintética.
4. Parsea RUT (módulo 11), IVA 19% y totales inconsistentes.
5. Exporta un Excel listo para cuadratura / auditoría.

## Arquitectura (microservicios)

| Servicio | Tecnología | Puerto |
|---|---|---|
| `web` | React + Nginx | 8080 |
| `api` | FastAPI + OpenCV + Tesseract + scikit-learn | 8000 |
| `db` | PostgreSQL 16 | 5432 |

## Cómo levantar

Requisitos: Docker Desktop.

```bash
cd "c:\Users\diego\Downloads\proyecto capton"
copy .env.example .env
docker compose up --build
```

Abra [http://localhost:8080](http://localhost:8080), cree una cuenta de empresa y suba una imagen de boleta/factura.

La primera arrancada de `api` entrena el modelo de caracteres (unos segundos) y lo deja en el volumen `capton_models`.

## Objetivos APT cubiertos

- Arquitectura Docker Compose: frontend, API y base de datos.
- Visión computacional para extraer montos, fechas, comercio y RUT.
- Algoritmo ML de reconstrucción de caracteres en zonas deterioradas.
- Exportación Excel para el departamento contable.
- Despliegue local (soberanía de datos).

## Desarrollo sin Docker (opcional)

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# Instale Tesseract OCR en Windows y agregue el ejecutable al PATH
set POSTGRES_HOST=localhost
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

El proxy de Vite reenvía `/api` a `http://127.0.0.1:8000`.

## Notas académicas

El prototipo prioriza **factibilidad de un semestre**: modelos livianos (OpenCV Telea + RandomForest) en lugar de GPU/Ollama. La pieza de inferencia tributaria (DV de RUT, IVA 19%) es deliberada: reconstruye datos faltantes con reglas de dominio, no solo con píxeles.
