import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_OUTPUT_PATH = os.path.abspath("City_Wide_ANPR_Intelligence_Platform_Documentation.pdf")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 40, letter[0] - 54, letter[1] - 40)
            self.drawString(54, letter[1] - 35, "City-Wide ANPR Intelligence & Traffic Analytics Platform | System Architecture")
        
        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, letter[0] - 54, 45)
        
        self.drawString(54, 32, "Confidential - Smart India Hackathon (SIH) Technical Documentation")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()

def generate_pdf():
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Brand Colors
    c_primary = colors.HexColor("#0F172A")    # Slate 900
    c_secondary = colors.HexColor("#0284C7")  # Sky Blue 600
    c_accent = colors.HexColor("#0D9488")     # Teal 600
    c_dark = colors.HexColor("#1E293B")       # Slate 800
    c_text = colors.HexColor("#334155")       # Slate 700
    c_card_bg = colors.HexColor("#F8FAFC")    # Slate 50
    c_border = colors.HexColor("#E2E8F0")     # Slate 200

    # Custom Typography Styles
    style_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=c_primary,
        spaceAfter=8
    )
    
    style_subtitle = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceAfter=15
    )

    style_h1 = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=20,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    style_h2 = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=c_text,
        spaceAfter=6
    )

    style_body_bold = ParagraphStyle(
        "Body_Bold",
        parent=style_body,
        fontName="Helvetica-Bold",
        textColor=c_dark
    )

    style_bullet = ParagraphStyle(
        "Bullet_Custom",
        parent=style_body,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    style_code = ParagraphStyle(
        "Code_Custom",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # ==========================
    # TITLE / HEADER BANNER
    # ==========================
    header_data = [
        [
            Paragraph("<b>CITY-WIDE ANPR INTELLIGENCE PLATFORM</b>", style_title),
        ],
        [
            Paragraph("Comprehensive Technical Architecture, Implementation Methodology & Technology Stack Documentation", style_subtitle)
        ]
    ]
    header_table = Table(header_data, colWidths=[504])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F9FF")),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#BAE6FD")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # Metadata Grid
    meta_data = [
        [
            Paragraph("<b>Project Domain:</b> Smart City Traffic AI & Homeland Security", style_body),
            Paragraph("<b>Target Accuracy:</b> &gt; 90% OCR Recognition Rate", style_body)
        ],
        [
            Paragraph("<b>Dataset Source:</b> Kaggle Car Number Plate Video Dataset", style_body),
            Paragraph("<b>System Core:</b> Real-time Multi-Camera Distributed Pipeline", style_body)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[252, 252])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # ==========================
    # 1. EXECUTIVE SUMMARY & PROBLEM STATEMENT
    # ==========================
    story.append(Paragraph("1. Executive Summary & Problem Context", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=8))
    story.append(Paragraph(
        "Modern urban metropolises deploy vast networks of CCTV and Automatic Number Plate Recognition (ANPR) cameras. "
        "However, legacy systems process feeds in <b>isolated silos</b>, performing disconnected plate detections without "
        "linking spatial and temporal relationships. This lack of centralized intelligence prevents law enforcement from "
        "reconstructing suspect travel trajectories and limits city traffic planners from extracting macro-level movement dynamics.",
        style_body
    ))
    story.append(Paragraph(
        "This project establishes a unified, end-to-end <b>City-Wide ANPR Intelligence & GIS Analytics Platform</b> "
        "that processes concurrent CCTV feeds in real time, delivers high-accuracy deep learning OCR across challenging environmental "
        "conditions (poor lighting, weather, motion blur, steep angles), reconstructs cross-camera vehicle trajectories, "
        "and visualizes macro traffic dynamics (Origin-Destination matrices, congestion bottlenecks, and GIS heatmaps).",
        style_body
    ))

    # ==========================
    # 2. KEY MODULES IMPLEMENTED
    # ==========================
    story.append(Spacer(1, 6))
    story.append(Paragraph("2. Implemented Core System Capabilities", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=8))

    modules = [
        ("A. High-Accuracy Deep Learning ANPR & OCR Engine", [
            "<b>Vehicle Detection:</b> YOLOv8 deep learning detector identifying Car, Motorcycle, Bus, and Truck classes with vehicle color classification.",
            "<b>License Plate Localization:</b> Fine-tuned YOLOv8 License Plate bounding box model trained on real-world Kaggle CCTV video footage.",
            "<b>Image Preprocessing & Normalization:</b> Contrast Limited Adaptive Histogram Equalization (CLAHE), Bilateral filtering for motion deblurring, and aspect ratio rectification.",
            "<b>Deep OCR & Positional Grammar Correction:</b> Deep Learning OCR (EasyOCR / CRNN) coupled with Indian HSRP syntax normalization (State codes, district codes, series rules, number disambiguation e.g., O/0, I/1, Z/2, B/8).",
            "<b>Multi-Frame Temporal Voting:</b> Aggregates plate readings across consecutive video frames to produce a single, high-confidence consensus plate, eliminating single-frame false positives."
        ]),
        ("B. Multi-Camera Real-Time Signal Processing Engine", [
            "<b>Concurrent Stream Architecture:</b> Multithreaded video processor handling simultaneous camera feeds across city junctions (Connaught Place, AIIMS Flyover, ITO Junction, DND Toll, etc.).",
            "<b>Real-time Ingestion & WebSocket Broadcast:</b> Sub-second event streaming pushing detection metadata to central FastAPI server and live dashboard clients."
        ]),
        ("C. Single Plate Spatial-Temporal Trajectory Reconstruction", [
            "<b>Chronological Journey Mapping:</b> Queries historical camera sightings for any queried license plate across time and space.",
            "<b>Geodesic Distance & Speed Computation:</b> Uses WGS-84 geodesic algorithms (Geopy/Haversine) to compute hop-by-hop travel times, inter-camera distances, and average speeds (km/h).",
            "<b>Cloned Plate / Route Anomaly Detection:</b> Flags physically impossible travel speeds between distant cameras, alerting operators to cloned plates."
        ]),
        ("D. Macro Traffic Analytics & GIS Dashboard", [
            "<b>Origin-Destination (OD) Matrix:</b> Aggregates vehicle movement patterns between city entry and exit points.",
            "<b>Congestion & Level of Service (LoS):</b> Real-time congestion index calculation based on vehicle throughput and sector speeds.",
            "<b>Geospatial Density Heatmaps:</b> Visual heatmaps overlaid on interactive Leaflet GIS city maps with temporal filtering."
        ]),
        ("E. Real-Time Alert & Hotlist Security Engine", [
            "<b>Automated Hotlist Matching:</b> Real-time matching against Stolen, Wanted, Revoked, and Suspicious vehicle registries.",
            "<b>Speed Limit Enforcement:</b> Instant alerts triggered when vehicles exceed camera zone speed thresholds.",
            "<b>Sound & Push Notifications:</b> Real-time visual and audio alerts on the monitoring terminal."
        ])
    ]

    for title, points in modules:
        story.append(Paragraph(title, style_h2))
        for pt in points:
            story.append(Paragraph(f"• {pt}", style_bullet))
        story.append(Spacer(1, 4))

    story.append(PageBreak())

    # ==========================
    # 3. TECHNICAL ARCHITECTURE & WORKFLOW
    # ==========================
    story.append(Paragraph("3. Technical Architecture & End-to-End Workflow", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=8))
    
    workflow_steps = [
        [
            Paragraph("<b>Stage</b>", style_body_bold),
            Paragraph("<b>Component / Engine</b>", style_body_bold),
            Paragraph("<b>Implementation Details & Methodology</b>", style_body_bold)
        ],
        [
            Paragraph("<b>1. Ingestion</b>", style_body),
            Paragraph("Multi-Camera Runner & Video Processor", style_body),
            Paragraph("Simultaneous decoding of video feeds (RTSP/CCTV/MP4). Frames sampled and batched to inference queue.", style_body)
        ],
        [
            Paragraph("<b>2. Detection</b>", style_body),
            Paragraph("YOLOv8 Detection Pipeline", style_body),
            Paragraph("YOLOv8 detects vehicle bounding boxes; plate detector isolates license plate ROI with sub-pixel precision.", style_body)
        ],
        [
            Paragraph("<b>3. Enhancement</b>", style_body),
            Paragraph("Adaptive Computer Vision Preprocessor", style_body),
            Paragraph("CLAHE contrast normalization, bilateral noise suppression, and morphological skew correction.", style_body)
        ],
        [
            Paragraph("<b>4. Recognition</b>", style_body),
            Paragraph("Deep OCR + HSRP Regex Engine", style_body),
            Paragraph("Character recognition powered by PyTorch EasyOCR deep neural network + Indian state/series syntactic validator.", style_body)
        ],
        [
            Paragraph("<b>5. Temporal Voting</b>", style_body),
            Paragraph("Multi-Frame Plate Aggregator", style_body),
            Paragraph("Sliding window voting resolves character-level character consensus, eliminating flickering & OCR jitter.", style_body)
        ],
        [
            Paragraph("<b>6. Backend & GIS</b>", style_body),
            Paragraph("FastAPI REST & WebSocket Hub", style_body),
            Paragraph("Detections ingested to SQLite/PostgreSQL. Trajectories, speeds, and hotlist alerts computed in real time.", style_body)
        ],
        [
            Paragraph("<b>7. Command UI</b>", style_body),
            Paragraph("React + Vite + Leaflet GIS Dashboard", style_body),
            Paragraph("Real-time CCTV grid, interactive map path reconstruction, traffic heatmaps, and alert center.", style_body)
        ]
    ]
    
    workflow_table = Table(workflow_steps, colWidths=[70, 130, 304])
    workflow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E0F2FE")),
        ('TEXTCOLOR', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(workflow_table)
    story.append(Spacer(1, 12))

    # ==========================
    # 4. COMPREHENSIVE TECH STACK
    # ==========================
    story.append(Paragraph("4. Comprehensive Technology Stack", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=8))

    stack_data = [
        [
            Paragraph("<b>Layer</b>", style_body_bold),
            Paragraph("<b>Technology / Framework</b>", style_body_bold),
            Paragraph("<b>Version</b>", style_body_bold),
            Paragraph("<b>Role & Responsibility</b>", style_body_bold)
        ],
        [
            Paragraph("<b>AI / Computer Vision</b>", style_body),
            Paragraph("Ultralytics YOLOv8<br/>OpenCV<br/>EasyOCR / PyTorch<br/>scikit-image", style_body),
            Paragraph("v8.4.x<br/>v5.0.x<br/>v1.7.x<br/>v0.26.x", style_body),
            Paragraph("Vehicle detection, plate localization, image enhancement, neural OCR, and motion deblurring.", style_body)
        ],
        [
            Paragraph("<b>Dataset & Training</b>", style_body),
            Paragraph("KaggleHub API<br/>PyTorch Torchvision", style_body),
            Paragraph("v1.0.x<br/>v2.13.x", style_body),
            Paragraph("Real car plate video dataset downloading, frame labeling, model fine-tuning and validation.", style_body)
        ],
        [
            Paragraph("<b>Backend API & WebSockets</b>", style_body),
            Paragraph("FastAPI<br/>Uvicorn<br/>WebSockets<br/>Pydantic", style_body),
            Paragraph("v0.141.x<br/>v0.52.x<br/>v17.1<br/>v2.13.x", style_body),
            Paragraph("Asynchronous microservices, sub-second event ingestion, real-time live push broadcasting, and request schemas.", style_body)
        ],
        [
            Paragraph("<b>Database & ORM</b>", style_body),
            Paragraph("SQLAlchemy ORM<br/>SQLite / PostgreSQL", style_body),
            Paragraph("v2.0.x<br/>v3.x", style_body),
            Paragraph("Persistent relational storage for camera registry, detection events, trajectory logs, and hotlists.", style_body)
        ],
        [
            Paragraph("<b>Spatial Analytics</b>", style_body),
            Paragraph("Geopy<br/>Pandas / Polars<br/>NumPy / SciPy", style_body),
            Paragraph("v2.5.x<br/>v3.0.x<br/>v2.5.x", style_body),
            Paragraph("WGS-84 geodesic distance, vehicle speed calculation, OD matrix aggregation, and density analytics.", style_body)
        ],
        [
            Paragraph("<b>Frontend Framework</b>", style_body),
            Paragraph("React 19<br/>Vite 8<br/>TailwindCSS 4", style_body),
            Paragraph("v19.2.x<br/>v8.2.x<br/>v4.3.x", style_body),
            Paragraph("High-performance reactive user interface, multi-tile surveillance grid, dark-mode glassmorphic theme.", style_body)
        ],
        [
            Paragraph("<b>GIS & Visualization</b>", style_body),
            Paragraph("Leaflet GIS<br/>Recharts<br/>Lucide React", style_body),
            Paragraph("v1.9.x<br/>v3.10.x<br/>v1.37.x", style_body),
            Paragraph("Interactive map trajectory routing, traffic heatmaps, congestion charts, and monitoring icons.", style_body)
        ],
        [
            Paragraph("<b>Package & Environment</b>", style_body),
            Paragraph("uv (Astral)<br/>Python 3.12", style_body),
            Paragraph("v0.6.x<br/>v3.12", style_body),
            Paragraph("Blazing fast virtual environment, deterministic lockfile management, and cross-platform execution.", style_body)
        ]
    ]

    stack_table = Table(stack_data, colWidths=[85, 120, 60, 239])
    stack_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E0F2FE")),
        ('TEXTCOLOR', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(stack_table)

    story.append(PageBreak())

    # ==========================
    # 5. API SPECIFICATIONS & REST ENDPOINTS
    # ==========================
    story.append(Paragraph("5. API Architecture & Key Endpoints", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=8))

    api_endpoints = [
        [
            Paragraph("<b>Method & Route</b>", style_body_bold),
            Paragraph("<b>Payload / Parameters</b>", style_body_bold),
            Paragraph("<b>Description & Output</b>", style_body_bold)
        ],
        [
            Paragraph("<b>POST</b><br/><code>/api/v1/detections/ingest</code>", style_body),
            Paragraph("<code>camera_id, plate_number, confidence, vehicle_type, vehicle_color, speed</code>", style_body),
            Paragraph("Ingests real-time detection event, checks hotlist, and broadcasts to WebSocket clients.", style_body)
        ],
        [
            Paragraph("<b>GET</b><br/><code>/api/v1/trajectories/{plate}</code>", style_body),
            Paragraph("<code>plate_number (path)</code>", style_body),
            Paragraph("Reconstructs chronological journey path, hops, inter-camera speeds, and cloned plate anomaly flags.", style_body)
        ],
        [
            Paragraph("<b>GET</b><br/><code>/api/v1/analytics/summary</code>", style_body),
            Paragraph("<code>hours (query, default 24)</code>", style_body),
            Paragraph("Returns city-wide traffic volume, active alert count, average network speed, and vehicle distribution.", style_body)
        ],
        [
            Paragraph("<b>GET</b><br/><code>/api/v1/analytics/heatmap</code>", style_body),
            Paragraph("<code>None</code>", style_body),
            Paragraph("Returns spatial coordinates with density weights for dynamic Leaflet GIS heatmap layers.", style_body)
        ],
        [
            Paragraph("<b>GET</b><br/><code>/api/v1/analytics/od-matrix</code>", style_body),
            Paragraph("<code>None</code>", style_body),
            Paragraph("Origin-Destination traffic flow matrix showing vehicle travel counts between camera nodes.", style_body)
        ],
        [
            Paragraph("<b>GET</b><br/><code>/api/v1/alerts</code>", style_body),
            Paragraph("<code>limit, unresolved_only</code>", style_body),
            Paragraph("Lists active security alerts, hotlist matches, speed limit violations, and cloned plate alerts.", style_body)
        ],
        [
            Paragraph("<b>WS</b><br/><code>/ws/live</code>", style_body),
            Paragraph("<code>WebSocket connection</code>", style_body),
            Paragraph("Full-duplex real-time stream broadcasting detection events, alerts, and camera telemetry.", style_body)
        ]
    ]

    api_table = Table(api_endpoints, colWidths=[130, 160, 214])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E0F2FE")),
        ('TEXTCOLOR', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(api_table)
    story.append(Spacer(1, 14))

    # ==========================
    # 6. HOW TO RUN & VERIFY
    # ==========================
    story.append(Paragraph("6. Deployment & Verification Quickstart", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=8))

    instructions = [
        ("Step 1: Start Backend Server", "<code>uv run python run_backend.py</code><br/>FastAPI backend starts at http://127.0.0.1:8000 with Swagger UI at /docs."),
        ("Step 2: Start Frontend Command Center", "<code>cd frontend &amp;&amp; npm run dev</code><br/>React + Vite dashboard starts at http://localhost:5173."),
        ("Step 3: Train & Validate Model on Kaggle Dataset", "<code>uv run python ai_pipeline/train_plate_detector.py</code><br/>Fine-tunes YOLO plate detector on real video frames and computes mAP@50 metrics."),
        ("Step 4: Run Multi-Camera Real-Time Pipeline", "<code>uv run python ai_pipeline/multi_camera_runner.py</code><br/>Streams real CCTV video feeds concurrently across all camera nodes and posts live detections.")
    ]

    for step_title, step_desc in instructions:
        story.append(Paragraph(f"<b>{step_title}</b>", style_h2))
        story.append(Paragraph(step_desc, style_body))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Repository & Source Code:</b> https://github.com/maviyashaikh25/sih",
        style_body_bold
    ))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF Successfully generated at: {PDF_OUTPUT_PATH}")

if __name__ == "__main__":
    generate_pdf()
