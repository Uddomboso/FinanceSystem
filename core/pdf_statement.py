"""
PDF Bank Statement Generator
Generates professional bank statements from Plaid and local transaction data.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime, date
from typing import List, Dict, Optional
from core.config import Config


def mask_account_id(account_id: str) -> str:
    """Mask account ID to show only last 4 characters"""
    if not account_id or len(account_id) <= 4:
        return "****"
    return f"****{account_id[-4:]}"


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"


def generate_bank_statement(
    output_path: str,
    user_id: int,
    start_date: date,
    end_date: date,
    transactions: List[Dict],
    checking_balance: float = 0.0,
    savings_balance: float = 0.0,
    checking_account_id: Optional[str] = None,
    savings_account_id: Optional[str] = None,
    commitments: Optional[List[Dict]] = None
) -> bool:
    """
    Generate a PDF bank statement.
    
    Args:
        output_path: Path to save the PDF file
        user_id: User ID
        start_date: Statement start date
        end_date: Statement end date
        transactions: List of transaction dicts with keys: date, description, amount, category_name, transaction_type
        checking_balance: Current checking account balance
        savings_balance: Current savings account balance
        checking_account_id: Checking account identifier (will be masked)
        savings_account_id: Savings account identifier (will be masked)
        commitments: Optional list of commitments dicts with keys: category_name, expected_amount
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Container for PDF elements
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#6B7280'),
            spaceAfter=24,
            alignment=TA_CENTER
        )
        
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1F2937'),
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        # Header
        story.append(Paragraph(f"{Config.APP_NAME}", title_style))
        story.append(Paragraph("Bank Statement", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Date range
        date_range_text = f"Statement Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        story.append(Paragraph(date_range_text, subtitle_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Account Summary Section
        story.append(Paragraph("Account Summary", section_style))
        
        account_data = []
        account_data.append(['Account Type', 'Account Number', 'Balance'])
        
        # Checking account
        checking_masked = mask_account_id(checking_account_id) if checking_account_id else "N/A"
        account_data.append(['Checking', checking_masked, format_currency(checking_balance)])
        
        # Savings account (if available)
        if savings_balance > 0 or savings_account_id:
            savings_masked = mask_account_id(savings_account_id) if savings_account_id else "N/A"
            account_data.append(['Savings', savings_masked, format_currency(savings_balance)])
        
        account_table = Table(account_data, colWidths=[2*inch, 2.5*inch, 2*inch])
        account_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
        ]))
        story.append(account_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Transactions Section
        story.append(Paragraph("Transactions", section_style))
        
        if not transactions:
            story.append(Paragraph("No transactions found for this period.", styles['Normal']))
        else:
            # Transaction table header
            trans_data = []
            trans_data.append(['Date', 'Description', 'Category', 'Amount'])
            
            # Add transactions
            for txn in transactions:
                txn_date = txn.get('date', '')
                if isinstance(txn_date, str):
                    try:
                        # Parse date string
                        if 'T' in txn_date:
                            txn_date = txn_date.split('T')[0]
                        date_obj = datetime.strptime(txn_date, '%Y-%m-%d').date()
                        date_str = date_obj.strftime('%m/%d/%Y')
                    except:
                        date_str = txn_date
                else:
                    date_str = str(txn_date)
                
                description = txn.get('description', 'N/A') or 'N/A'
                # Truncate long descriptions
                if len(description) > 50:
                    description = description[:47] + "..."
                
                category = txn.get('category_name', 'Uncategorized') or 'Uncategorized'
                amount = float(txn.get('amount', 0) or 0)
                txn_type = txn.get('transaction_type', 'expense')
                
                # Format amount with sign based on type
                if txn_type == 'income':
                    amount_str = f"+{format_currency(amount)}"
                    amount_color = colors.HexColor('#10B981')  # Green for income
                else:
                    amount_str = f"-{format_currency(amount)}"
                    amount_color = colors.HexColor('#EF4444')  # Red for expense
                
                trans_data.append([date_str, description, category, amount_str])
            
            # Create transaction table
            trans_table = Table(trans_data, colWidths=[1.2*inch, 3*inch, 1.5*inch, 1.3*inch])
            
            # Style transaction table
            trans_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
            ]
            
            # Color-code amounts (income green, expense red)
            for i in range(1, len(trans_data)):
                amount_cell = trans_data[i][3]
                if amount_cell.startswith('+'):
                    trans_style.append(('TEXTCOLOR', (3, i), (3, i), colors.HexColor('#10B981')))
                elif amount_cell.startswith('-'):
                    trans_style.append(('TEXTCOLOR', (3, i), (3, i), colors.HexColor('#EF4444')))
            
            trans_table.setStyle(TableStyle(trans_style))
            story.append(trans_table)
        
        story.append(Spacer(1, 0.3*inch))
        
        # Optional Commitments Summary (if provided)
        if commitments and len(commitments) > 0:
            story.append(Paragraph("Commitments Summary", section_style))
            
            commit_data = []
            commit_data.append(['Category', 'Expected Amount'])
            
            for commit in commitments:
                category = commit.get('category_name', 'N/A') or 'N/A'
                amount = float(commit.get('expected_amount', 0) or 0)
                commit_data.append([category, format_currency(amount)])
            
            commit_table = Table(commit_data, colWidths=[4*inch, 2*inch])
            commit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
            ]))
            story.append(commit_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Spacer(1, 0.2*inch))
        footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return True
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating PDF statement: {e}")
        return False

