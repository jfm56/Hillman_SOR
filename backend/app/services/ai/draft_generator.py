import time
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.report import Report
from app.models.image import Image
from app.models.document import Document
from app.models.template import ReportTemplate
from app.services.ai.rag import build_rag_context
from app.services.ai.ai_learning import log_ai_interaction, build_learning_context
from app.core.config import settings


async def get_default_template(db: AsyncSession, template_type: str = "sor") -> Optional[ReportTemplate]:
    """Get the default template for a given type."""
    result = await db.execute(
        select(ReportTemplate)
        .where(ReportTemplate.template_type == template_type)
        .where(ReportTemplate.is_default == True)
        .where(ReportTemplate.is_active == True)
    )
    return result.scalar_one_or_none()


BASE_SYSTEM_PROMPT = """You are a professional construction consultant writing a Site Observation Report for Hillmann Consulting.

Your writing must:
1. Use formal, technical language appropriate for engineering reports
2. Reference specific evidence (photos, documents) with citations like [Evidence: filename]
3. Avoid speculation - only state what was directly observed
4. Use passive voice for observations ("It was observed that...")
5. Include specific dates and locations when available
6. Follow the EXACT format and structure of the provided template

CRITICAL RULES:
- Never fabricate observations not supported by the input data
- Always cite the source of each observation
- Flag any uncertainty with "appears to" or "further investigation recommended"
- Use standard construction terminology
- Fill in ALL highlighted/bracketed fields from the template with actual project data
- Maintain the exact formatting, headers, and structure from the template

SOR WORKFLOW CONTEXT (Hillmann SOP):
Before 1st Site Visit, the following should be reviewed from Plan and Cost Review (PCR):
- Project scope
- Client identity (bank, investor, or syndicator) and their role
- Developer/Borrower/Sponsor information
- General Contractor details
- Project schedule and milestones
- Construction Contract terms (Retainage percentage, Completion requirements)
- Outstanding items from PCR (unsigned contracts, pending permits, design items not received)

Monthly Reporting Requirements:
- Attend site visits each month
- Review requisition at the site/design meeting
- Document all observations with photo evidence
- Track progress against schedule and budget
- Note any items requiring follow-up from previous SOR

AIA G702/G703 PAYMENT APPLICATION STRUCTURE:
The monthly requisition follows AIA G702 (Application for Payment) and G703 (Continuation Sheet) format:

G702 Key Fields:
- Original Contract Sum
- Net Change by Change Orders
- Contract Sum to Date
- Total Completed & Stored to Date
- Retainage (% of Completed Work, % of Stored Material)
- Total Earned Less Retainage
- Previous Certificates for Payment
- Current Payment Due
- Balance to Finish Including Retainage

G703 CSI Division Breakdown (Schedule of Values):
- Div 2: Site Work (Demolition, Excavation, Foundations, Paving, Landscaping)
- Div 3: Concrete (Superstructure, Precast)
- Div 4: Masonry (Unit Masonry, Architectural Stone, Brick)
- Div 5: Metals (Structural Steel, Miscellaneous/Ornamental Metals)
- Div 6: Wood & Plastic (Rough/Finish Carpentry, Millwork)
- Div 7: Thermal & Moisture Protection (Roofing, Waterproofing, Insulation, Fireproofing)
- Div 8: Doors & Windows (HM Doors, Wood Doors, Hardware, Storefronts, Curtain Wall)
- Div 9: Finishes (Drywall, Tile, Ceilings, Flooring, Paint)
- Div 10: Specialties (Toilet Partitions, Signage, Accessories)
- Div 11: Equipment (Appliances, Loading Dock)
- Div 12: Furnishings (Casework, Window Treatment)
- Div 13: Special Construction (Pools, Amenity Spaces)
- Div 14: Conveying Systems (Elevators, Lifts)
- Div 15: Mechanical (Fire Protection, Plumbing, HVAC)
- Div 16: Electrical (Power, Lighting, IT, Security)
- General Requirements, Overhead, Profit, CM/GC Fee, Contingency

For each line item track: Scheduled Value, Work Completed (Previous + This Period), Materials Stored, Total %, Balance to Finish

Change Orders (AIA G701):
- Track PCO (Potential Change Order) and approved CO numbers
- Document additions and deductions to contract sum
- Note impact on Contract Time and Substantial Completion date
- Change Orders must be signed by Owner, Architect, and General Contractor

Offsite Stored Materials Funding Requirements:
- Inventory tracking form (initial amount and amounts used monthly)
- Bill of Sale showing unencumbered clear title to Borrower
- Certificate of Insurance from storage facility
- Photos of materials clearly tagged for specific project

Retainage Release Requirements (End of Project):
- Consent of Surety
- Temporary Certificate of Occupancy (TCO)
- Architect's G704 Certificate of Substantial Completion
- Architect's costed punchlist
- Any retainage exemptions require acknowledgement from Owner, GC, Lender, and Investor

Testing/Inspection Reports:
- Controlled Testing reports
- Inspection reports
- Engineering certifications
- Hillmann must be on distribution list for all reports

SOR WORKFLOW (Step-by-Step Process):
1. Get Assigned SOR → Review Client Specific Requirements
2. Review Final PCR (Plan and Cost Review)
3. Set Up SOR #1 with PCR Info
4. Check if Site Visit Already Scheduled:
   - If Yes: Review Pencil AIA and Attend Site Visit
   - If No: Coordinate with Site Contact, Request OAC Meeting Invites
5. Send Intro Email to Project Team and Typical Monthly RFI
6. Try to Get All Questions Answered at the Meeting
7. Complete Photo File and Begin Drafting Report
8. If Additional Comments/Questions: Reach Out to Project Team ASAP
9. Receive Executed Draw Documents and Complete Report
10. Order Invoice
11. Issue Completed Report (Email or Upload) and Invoice

Required Documents by Contract Type:

GMP (Guaranteed Maximum Price) Projects require:
- GC AIA 702 & 703
- GC Lien Waiver
- Subcontractor AIAs
- Subcontractor Lien Waivers
- Up to Date Buyout Log
- Reallocation Log
- Up to Date Schedule
- PCO Log
- Executed Change Orders
- Stored Material Back-up

Non-GMP Projects require:
- GC AIA 702 & 703
- GC Lien Waiver
- Up to Date Schedule
- PCO Log
- Executed Change Orders
- Stored Material Back-up

STORED MATERIALS TRACKING FORMAT:
Standard blurb: "Offsite Stored Material Requests are summarized as follows. No site visits were conducted unless noted otherwise. Funding of offsite stored material is at the Lender's discretion."

Stored Materials Table Columns:
| Description of Stored Material | Storage Location | Opening Inventory | Additions to Inventory | Usage of Inventory | Closing Inventory |

Required Documentation for Offsite Stored Materials:
a. Invoice or Receipt from Subcontractor/Supplier
b. Photographs of material with labeling
c. Insurance Certificate with client named as additionally insured party

Track inventory values showing opening balance, additions, usage, and closing balance for each material type.

CLIENT-SPECIFIC REQUIREMENTS:

BERKADIA AFFORDABLE TAX CREDIT SOLUTIONS (BATCS) Requirements:
Questions to Address in Report:
- Are there products/design elements representing reduced quality or value?
- Is anything unique compared to standard multi-family?
- Do value engineering items represent reduction in quality?
- Do credit add alternates represent reduction in quality?
- Does construction schedule include weather days?
- Does schedule include float time for COVID-19 delays?
- Is heating/cooling adequate for the location?
- Have all ADA requirements been met?

BATCS Special Requirements:
- Verify unit mix table matches final construction drawings
- Include 15-year replacement reserve table
- Review and comment on warranty period
- Review add alternates and allowances for deferred submittals

BATCS Monitoring Requirements:
- Reports delivered within 15 business days after site visit
- Attend monthly payment application meetings (in person or virtual)
- Review all Change Orders for validity, pricing, and quality impact
- Review schedule updates and delays for completion impact

Walk-Through Percentage Requirements (by unit count):
| Total Units | Walk-Through % |
| 0-99        | 75%           |
| 100-199     | 50%           |
| 200+        | 30%           |
| Gut Rehab   | 30%           |
| Down Units  | 100%          |
- Multi-building: Units in each building per % above
- Scattered Site: All sites/parcels per % above
- Sample of each unit type must be inspected

Required Photo Documentation:
- Signage
- Typical building front
- Property frontage
- Apartment interior
- Amenities
- Major building systems
- Deferred maintenance and life safety items
- Extraordinary repair items requiring capital expenditure
- All critical or substantial issues noted

PROJECT DESIGN AND CONSTRUCTION CHECKLIST Fields:
Project Info: Name, Units, Stories, Buildings, Year Built, Acres, Density, Occupancy Profile (Family/Senior/Other)
Tax Credit Application: Yes/No verification
Construction Status: Not yet built, Under construction, Under renovation, Complete
Info Source: Actual, Plans, Developer, Comparable, Earlier phase

Utilities Verification:
- Sewer: sewer/septic/gravity/pump
- Gas service: Yes/Cable
- Utility lines: overhead/underground

Foundation Types: concrete/block/stone/partial bsmt/full bsmt/crawl space
Slab: reinforced/on grade/honches/post-tensioned slab
Structure: wood/steel/masonry
Exterior studs with dimensions, CMU, Interior studs

Roof Types: Flat/Mansard/Pitched (with pitch ratio and sheathing)
Frame: Wood frame/pre-fab trusses/steel trusses
Roofing: fiberglass/asphalt/membrane/wood/other

CAPITAL ONE - Off-Site Stored Materials Documentation Requirements:
1. Invoice/Purchase Order must include:
   - Date of order/purchase
   - Name of supplier and purchaser
   - Project for which materials purchased
   - Detailed list with quantity, unit cost, total cost (including taxes, shipping)
   - Amount paid and/or payment terms
   - Shipping date and address (if applicable)

2. Bill of Sale - Evidence ownership transfers to Borrower upon payment

3. Storage Location - Name and address required

4. Insurance Requirements:
   - Storage location must be insured (and bonded if applicable)
   - Materials must be specifically insured for their value
   - Materials must remain insured until delivered to project site
   - Capital One must be listed as additional insured on certificate

5. Photo Requirements:
   - Show storage facility matches documentation
   - Clearly show what materials/equipment are stored
   - Show materials are segregated from other items/inventory
   - Show materials are identified for the specific project
   - Show quantities consistent with invoice for value confirmation

6. Written Explanation required for why materials need advance payment and off-site storage
   (must demonstrate sound construction/business rationale)

Note: Lender reserves right to engage third-party consultant at Borrower's expense to verify materials.

JPMORGAN CHASE - Stored Materials Funding Process:
1. AIA 703 must indicate the line item and specific amount requested
2. Invoice/Bill of Sale must:
   - Match AIA 703 amount EXACTLY
   - Note project name
   - Describe stored materials including quantities
3. Certificate of Insurance must:
   - Name Owner and Lender(s) as Additional Insured
   - Name Lender(s) as Loss Payee
   - Include endorsement evidencing Additional Insured/Loss Payee
   - Name the project and material stored
4. Verification: Inspector must verify materials at storage location OR contractor/supplier provides photos
   - Materials must be marked for specific project
   - Identified with type and quantity

PROJECT CLOSEOUT DOCUMENTATION CHECKLIST:
Required documents for project completion (with Dated and Accepted Y/N tracking):
1. Certificate of Occupancy
2. Certificate of Substantial Completion (AIA G704)
3. As-Built ALTA Survey
4. Final Lien Waivers
5. Consent of Surety to Final Payment (AIA G707)
6. Contractor's Affidavit of Payment of Debts and Claims (AIA G706)
7. Contractor's Affidavit of Release of Liens (AIA G706A)
8. Architect's verification that punchlist work is complete
9. Notice of completion duly recorded with the county (if applicable)
10. Any environmental reports generated (if applicable)

Note: All information should be previewed and approved by Owner and Architect prior to submitting."""


def build_system_prompt(template: Optional[ReportTemplate] = None) -> str:
    """Build system prompt incorporating template style guide."""
    prompt = BASE_SYSTEM_PROMPT
    
    if template and template.style_guide:
        style = template.style_guide
        style_instructions = "\n\nTEMPLATE STYLE REQUIREMENTS:"
        
        if style.get("common_phrases"):
            style_instructions += f"\n- Use these phrases where appropriate: {', '.join(style['common_phrases'])}"
        
        if style.get("terminology"):
            style_instructions += f"\n- Use this terminology: {', '.join(style['terminology'])}"
        
        if style.get("tone"):
            style_instructions += f"\n- Maintain a {style['tone']} tone throughout"
        
        prompt += style_instructions
    
    return prompt


async def generate_section_draft(
    db: AsyncSession,
    report: Report,
    section_type: str,
    options: dict,
    user_id: Optional[UUID] = None,
) -> dict:
    """Generate an AI draft for a report section, learning from past interactions."""
    start_time = time.time()
    
    # Get the default template for this report type
    template_type = options.get("template_type", "sor")
    template = await get_default_template(db, template_type)
    
    # Gather context data
    context_parts = []
    evidence_references = []
    
    # Add template content as reference if available
    if template and template.extracted_text:
        template_section = f"""TEMPLATE FORMAT TO FOLLOW:
The following is the template format you MUST follow exactly. Fill in all bracketed/highlighted fields with actual project data:

{template.extracted_text[:3000]}

IMPORTANT: Replace all placeholder text (like [Project Name], [Date], highlighted sections) with actual values from the project context below."""
        context_parts.append(template_section)
    
    # 1. Get project images with AI analysis
    if options.get("include_images", True):
        image_result = await db.execute(
            select(Image)
            .where(Image.project_id == report.project_id)
            .where(Image.ai_description.isnot(None))
        )
        images = image_result.scalars().all()
        
        if images:
            image_descriptions = []
            for img in images[:10]:  # Limit to 10 images
                desc = f"- {img.original_filename}: {img.ai_description}"
                if img.building:
                    desc = f"- {img.original_filename} ({img.building.name}): {img.ai_description}"
                image_descriptions.append(desc)
                evidence_references.append({
                    "type": "image",
                    "id": str(img.id),
                    "filename": img.original_filename,
                })
            
            context_parts.append("PHOTO OBSERVATIONS:\n" + "\n".join(image_descriptions))
    
    # 2. Get parsed documents
    if options.get("include_documents", True):
        doc_result = await db.execute(
            select(Document)
            .where(Document.project_id == report.project_id)
            .where(Document.is_processed == True)
        )
        documents = doc_result.scalars().all()
        
        if documents:
            doc_summaries = []
            for doc in documents:
                if doc.parsed_data:
                    summary = f"- {doc.original_filename} ({doc.document_type}): "
                    if doc.document_type == "prior_sor":
                        summary += f"Prior report from {doc.parsed_data.get('report_date', 'unknown date')}"
                    elif doc.document_type == "cost_review":
                        summary += f"Budget: ${doc.parsed_data.get('current_budget', 0):,}, {doc.parsed_data.get('percent_complete', 0)}% complete"
                    else:
                        summary += "Parsed successfully"
                    doc_summaries.append(summary)
                    evidence_references.append({
                        "type": "document",
                        "id": str(doc.id),
                        "filename": doc.original_filename,
                        "document_type": doc.document_type,
                    })
            
            if doc_summaries:
                context_parts.append("DOCUMENT DATA:\n" + "\n".join(doc_summaries))
    
    # 3. Get RAG examples and learned context
    rag_context = ""
    learning_context = ""
    image_context = {}
    
    if options.get("use_rag", True):
        # Build context from image analyses
        if images:
            for img in images:
                if img.ai_analysis:
                    if img.ai_analysis.get("conditions"):
                        image_context.setdefault("conditions", []).extend(img.ai_analysis["conditions"])
                    if img.ai_analysis.get("building_type"):
                        image_context["building_type"] = img.ai_analysis["building_type"]
        
        rag_context = await build_rag_context(section_type, image_context)
    
    # 4. Get learned examples from past AI interactions
    if options.get("use_learning", True):
        learning_context = await build_learning_context(db, section_type, image_context)
    
    # 5. Build the prompt with template instructions
    template_instruction = ""
    required_fields_text = ""
    
    if template:
        template_instruction = """
CRITICAL: Follow the uploaded template format EXACTLY. The template shows:
- The exact section headers and structure to use
- The formatting and layout expected
- Placeholder fields (in brackets or highlighted) that must be filled with real data
"""
        # Add required fields from template structure
        if template.structure and template.structure.get("required_fields"):
            fields = template.structure["required_fields"]
            required_fields_text = "\nREQUIRED SOR DATA POINTS (per Hillmann Guidelines):\n"
            for f in fields:
                required_fields_text += f"- {f['label']} ({f['frequency']})\n"
            required_fields_text += "\nInclude ALL applicable data points in the report. Mark any missing items as 'Not provided' or 'Pending'.\n"
    
    user_prompt = f"""Generate the {section_type.replace('_', ' ').title()} section for this Site Observation Report.
{template_instruction}{required_fields_text}
PROJECT CONTEXT:
- Report Number: {report.report_number}
- Inspection Date: {report.inspection_date}
- Report Date: {report.report_date}
{f'- Weather: {report.weather_conditions}' if report.weather_conditions else ''}
{f'- Personnel: {report.personnel_on_site}' if report.personnel_on_site else ''}

{chr(10).join(context_parts)}

{rag_context}

{learning_context}

Generate the {section_type.replace('_', ' ').title()} section following the exact format from the template.
Include [Evidence: filename] citations for all observations.
Return only the section content, no additional formatting."""

    # Build system prompt with template style
    system_prompt = build_system_prompt(template)
    
    # Use local LLM or OpenAI
    input_tokens = 0
    output_tokens = 0
    
    if settings.USE_LOCAL_LLM:
        from app.services.ai.local_llm import generate_completion
        content = await generate_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=2000,
        )
        model_used = f"local:{settings.LOCAL_MODEL}"
    else:
        from app.services.ai.openai_client import get_openai_client
        client = get_openai_client()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.3,
        )
        content = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        model_used = settings.OPENAI_MODEL
    
    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Log this interaction for future learning
    await log_ai_interaction(
        db=db,
        user_id=user_id,
        interaction_type="draft_generation",
        model_name=model_used,
        prompt=user_prompt[:5000],  # Truncate very long prompts
        response=content,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        project_id=report.project_id,
        report_id=report.id,
        status="success",
    )
    
    return {
        "content": content,
        "evidence_references": evidence_references,
        "tokens_used": input_tokens + output_tokens,
        "model": model_used,
        "learned_from": len(learning_context) > 0,
    }
