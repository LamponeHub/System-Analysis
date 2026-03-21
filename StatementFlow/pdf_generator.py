from weasyprint import HTML, CSS
from io import BytesIO
from datetime import datetime
import models

def generate_statement_pdf(statement: models.Statement) -> bytes:
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 2cm; }}
            body {{ font-family: "Times New Roman", serif; font-size: 14pt; line-height: 1.5; }}
            .header-right {{ text-align: right; margin-bottom: 40px; }}
            .title {{ text-align: center; font-weight: bold; margin: 30px 0; text-transform: uppercase; }}
            .content {{ text-align: justify; text-indent: 40px; }}
            .footer {{ margin-top: 60px; display: flex; justify-content: space-between; }}
            .signature-line {{ border-top: 1px solid black; width: 200px; text-align: center; padding-top: 5px; }}
            .status-badge {{ 
                display: inline-block; 
                padding: 5px 15px; 
                border-radius: 3px;
                font-size: 12pt;
                margin-bottom: 20px;
            }}
            .status-draft {{ background: #f0f0f0; color: #666; }}
            .status-submitted {{ background: #fff3cd; color: #856404; }}
            .status-answered {{ background: #d4edda; color: #155724; }}
        </style>
    </head>
    <body>
        <div class="header-right">
            <p>Начальнику {statement.target_department}</p>
            <p>от гр. {statement.applicant_name},</p>
            <p>проживающего по адресу:</p>
            <p>{statement.applicant_address}</p>
            <p>Тел: _______________</p>
        </div>
        
        <div class="status-badge status-{statement.status.value}">
            Статус: {statement.status.value.upper()}
        </div>
        
        <div class="title">ЗАЯВЛЕНИЕ</div>
        
        <div class="content">
            {statement.description}
            <br><br>
            На основании изложенного, руководствуясь ст. 141 УПК РФ, прошу принять данное заявление, 
            провести проверку и возбудить уголовное дело.
            <br><br>
            Об ответственности за заведомо ложный донос по ст. 306 УК РФ предупрежден(а).
        </div>
        
        <div class="footer">
            <div>Дата: {datetime.now().strftime('%d.%m.%Y')}</div>
            <div class="signature-line">Подпись / {statement.applicant_name}</div>
        </div>
    </body>
    </html>
    """
    
    pdf = HTML(string=html_content).write_pdf()
    return pdf