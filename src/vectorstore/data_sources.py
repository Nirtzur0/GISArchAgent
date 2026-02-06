"""
Sample Regulation Data Sources

Contains sample regulation data for initializing the vector database.
This data can be extended or replaced with data from other sources.
"""

from src.domain.entities.regulation import RegulationType


# Default sample regulations for system initialization
DEFAULT_SAMPLE_REGULATIONS = [
    {
        "id": "reg_building_height_residential",
        "type": RegulationType.LOCAL,
        "title": "Building Height Regulations for Residential Areas",
        "content": """
Building height regulations for residential zones:
- Zone A (High-rise): Maximum 25 floors or 75 meters
- Zone B (Medium-rise): Maximum 8 floors or 24 meters  
- Zone C (Low-rise): Maximum 3 floors or 10 meters

Additional requirements:
- Ground floor height minimum 3.5 meters for commercial use
- Residential floor height minimum 2.8 meters
- Setback requirements increase with building height
- Shadow analysis required for buildings over 5 floors
        """,
        "summary": "Defines maximum building heights for different residential zones",
        "jurisdiction": "national",
    },
    {
        "id": "reg_parking_requirements",
        "type": RegulationType.LOCAL,
        "title": "Parking Space Requirements",
        "content": """
Minimum parking requirements per unit type:
- Residential apartment: 1.5 spaces per unit
- Studio apartment: 1 space per unit
- Commercial office: 1 space per 50 sqm
- Retail space: 1 space per 30 sqm
- Restaurant/Cafe: 1 space per 20 sqm + delivery zone

Parking space dimensions:
- Standard space: 2.5m x 5.0m minimum
- Accessible space: 3.5m x 5.0m minimum
- Motorcycle space: 1.5m x 2.5m minimum

Reduction allowed:
- Near public transport (500m): Up to 20% reduction
- City center zones: Up to 30% reduction
- Car-sharing program: Up to 15% reduction
        """,
        "summary": "Parking space requirements for different building types",
        "jurisdiction": "national",
    },
    {
        "id": "reg_setback_requirements",
        "type": RegulationType.LOCAL,
        "title": "Building Setback Requirements",
        "content": """
Minimum setback distances from property lines:

Front setback (street-facing):
- Residential zones: 4 meters minimum
- Commercial zones: 2 meters minimum
- Industrial zones: 6 meters minimum

Side setback:
- Buildings up to 3 floors: 2 meters
- Buildings 4-8 floors: 3 meters
- Buildings over 8 floors: 4 meters

Rear setback:
- All zones: 3 meters minimum
- Additional 1 meter per floor above 3 floors

Special conditions:
- Setbacks may be reduced for infill development
- Corner lots have reduced side setback requirements
- Heritage areas require increased setbacks
        """,
        "summary": "Required distances from property boundaries for construction",
        "jurisdiction": "national",
    },
    {
        "id": "reg_floor_area_ratio",
        "type": RegulationType.LOCAL,
        "title": "Floor Area Ratio (FAR) Regulations",
        "content": """
Maximum Floor Area Ratio by zone:

Residential zones:
- R1 (Low density): FAR 0.6
- R2 (Medium density): FAR 1.2
- R3 (High density): FAR 2.0
- R4 (Urban center): FAR 3.0

Mixed-use zones:
- M1: FAR 1.8
- M2: FAR 2.5
- M3: FAR 3.5

Bonuses available:
- Green building certification: +10% FAR
- Affordable housing inclusion: +15% FAR
- Public space provision: +20% FAR
- Heritage preservation: +10% FAR

Maximum combined bonus: 30% above base FAR
        """,
        "summary": "Floor area ratio limits and bonus provisions",
        "jurisdiction": "national",
    },
    {
        "id": "reg_lot_coverage",
        "type": RegulationType.LOCAL,
        "title": "Lot Coverage Regulations",
        "content": """
Maximum lot coverage percentages:

Residential zones:
- Single family: 40% maximum
- Duplex/Triplex: 50% maximum
- Multi-family: 60% maximum
- High-rise: 70% maximum (podium)

Non-residential:
- Commercial: 80% maximum
- Industrial: 70% maximum
- Institutional: 50% maximum

Open space requirements:
- Minimum 20% landscaped area
- At least 50% of open space must be permeable
- Trees required: 1 per 100 sqm of lot area

Exceptions:
- Urban infill sites may increase coverage by 10%
- Heritage buildings may exceed limits
        """,
        "summary": "Maximum building footprint as percentage of lot area",
        "jurisdiction": "national",
    },
    {
        "id": "reg_green_building",
        "type": RegulationType.TAMA,
        "title": "Green Building Standards",
        "content": """
Mandatory green building requirements:

Energy efficiency:
- Buildings over 1000 sqm must achieve minimum 20% energy savings
- Solar panels required for 15% of roof area
- High-efficiency HVAC systems mandatory
- LED lighting in common areas

Water conservation:
- Low-flow fixtures required (max 6L per flush)
- Rainwater collection for irrigation
- Greywater recycling for buildings over 5000 sqm

Materials:
- Minimum 20% recycled content in materials
- Low-VOC paints and finishes
- Locally sourced materials preferred (within 500km)

Certification:
- Buildings over 5000 sqm require green building certification
- LEED, Green Star, or equivalent accepted
        """,
        "summary": "Environmental and sustainability requirements for new construction",
        "jurisdiction": "national",
    },
    {
        "id": "reg_accessibility",
        "type": RegulationType.TAMA,
        "title": "Accessibility Requirements",
        "content": """
Universal accessibility standards:

Building access:
- All public buildings must have wheelchair access
- Ramps: Maximum slope 1:12, minimum width 1.2m
- Elevators required in buildings over 2 floors
- Accessible parking: Minimum 5% of total spaces

Doorways and corridors:
- Minimum door width: 90cm clear opening
- Corridor width: 120cm minimum, 150cm for two-way
- Turning radius: 150cm diameter minimum

Restrooms:
- Accessible restroom required on each floor
- Grab bars and appropriate fixtures
- Minimum 180cm turning radius

Visual and auditory:
- Braille signage at entrance and elevators
- Audio announcements in elevators
- Visual fire alarms required
- Contrasting colors for safety features
        """,
        "summary": "Requirements for accessible design in all buildings",
        "jurisdiction": "national",
    },
    {
        "id": "reg_fire_safety",
        "type": RegulationType.TAMA,
        "title": "Fire Safety Regulations",
        "content": """
Fire safety requirements by building type:

Fire-resistant construction:
- Buildings over 4 floors: Type I or II construction
- Fire walls required between units in multi-family
- Fire-rated doors (45-90 minutes) in corridors

Egress requirements:
- Two means of egress for floors over 1000 sqm
- Exit signs illuminated and visible from all points
- Maximum travel distance to exit: 45 meters
- Stairwell width: 120cm minimum

Fire suppression:
- Sprinklers required in buildings over 8 floors
- Fire extinguishers every 30 meters
- Standpipes in high-rise buildings
- Fire hydrants within 100 meters

Detection and alarm:
- Smoke detectors in all residential units
- Central alarm system in multi-family buildings
- Emergency lighting in exit paths
- Monthly testing required
        """,
        "summary": "Fire safety and life safety code requirements",
        "jurisdiction": "national",
    },
    {
        "id": "reg_noise_control",
        "type": RegulationType.LOCAL,
        "title": "Noise Control Standards",
        "content": """
Maximum allowable noise levels:

Residential areas:
- Daytime (7am-10pm): 55 dB(A)
- Nighttime (10pm-7am): 45 dB(A)

Mixed-use areas:
- Daytime: 60 dB(A)
- Nighttime: 50 dB(A)

Commercial/Industrial:
- Daytime: 70 dB(A)
- Nighttime: 60 dB(A)

Sound insulation requirements:
- Party walls: STC 55 minimum
- Floor/ceiling: STC 50 + IIC 50
- Windows on busy streets: STC 30 minimum

Construction noise:
- Permitted hours: 7am-6pm weekdays
- Saturday work requires special permit
- No work on Sundays and holidays
- Noise barriers required near residential
        """,
        "summary": "Noise level limits and sound insulation requirements",
        "jurisdiction": "national",
    },
    {
        "id": "reg_signage_advertising",
        "type": RegulationType.LOCAL,
        "title": "Signage and Advertising Regulations",
        "content": """
Sign regulations by zone:

Residential zones:
- Home business signs: Maximum 0.5 sqm
- No illuminated signs allowed
- One sign per property

Commercial zones:
- Wall signs: Maximum 10% of wall area
- Freestanding signs: Maximum 6 meters height
- Projecting signs: Maximum 1 meter projection
- Digital displays: Brightness limits apply

Sign construction:
- Wind load calculations required for large signs
- Proper electrical certification for illuminated signs
- Regular maintenance and inspection required

Prohibited signs:
- Flashing or animated signs near residential
- Signs that obstruct traffic visibility
- Signs on public property without permit
- Signs that mimic traffic signals
        """,
        "summary": "Regulations for commercial signage and advertising",
        "jurisdiction": "local",
    },
    # Hebrew / iPlan-like samples (deterministic + test-friendly)
    {
        "id": "iplan_sample_jerusalem_101_0121850",
        "type": RegulationType.LOCAL,
        "title": "תכנית 101-0121850 - שינוי קו בניין (ירושלים)",
        "content": """
תכנית מקומית לדוגמה (מדמה נתוני iPlan)

מספר תכנית: 101-0121850
רשות/עיר: ירושלים
מחוז: ירושלים
סוג תכנית: תכנית מתאר מקומית
סטטוס: בבדיקה תכנונית

תקציר:
שינוי קו בניין בבניין קיים, תוספת שטחים והבהרות הוראות.
        """.strip(),
        "summary": "דוגמה לתכנית עם מטא-דאטה עירוני",
        "jurisdiction": "ירושלים",
        "metadata": {
            "plan_number": "101-0121850",
            "plan_type": "תכנית מתאר מקומית",
            "municipality": "ירושלים",
            "municipality_name": "ירושלים",
            "city": "ירושלים",
            "district": "ירושלים",
            "status": "בבדיקה תכנונית",
            "source": "sample_iplan",
        },
    },
    {
        "id": "iplan_sample_tel_aviv_123_4567890",
        "type": RegulationType.LOCAL,
        "title": "תכנית 123-4567890 - מגורים ומסחר (תל אביב-יפו)",
        "content": """
תכנית לדוגמה (מדמה נתוני iPlan)

מספר תכנית: 123-4567890
רשות/עיר: תל אביב-יפו
מחוז: תל אביב
סוג תכנית: תכנית מפורטת
סטטוס: תכנית שאושרה (מתקדמות)

יעדים:
1. תוספת יחידות דיור באזור עירוני.
2. שילוב מסחר בקומת קרקע.
3. שיפור נגישות הולכי רגל.

הוראות עיקריות:
- שימושים: מגורים, מסחר, ציבור.
- חניה: בהתאם לתקן חניה עירוני ולהנחיות הוועדה המקומית.
- קווי בניין: לפי תרשים נספח.
        """.strip(),
        "summary": "דוגמה לתכנית עם מגוון מונחים (כולל חניה)",
        "jurisdiction": "תל אביב-יפו",
        "metadata": {
            "plan_number": "123-4567890",
            "plan_type": "תכנית מפורטת",
            "municipality": "תל אביב-יפו",
            "municipality_name": "תל אביב-יפו",
            "city": "תל אביב-יפו",
            "district": "תל אביב",
            "status": "תכנית שאושרה (מתקדמות)",
            "source": "sample_iplan",
        },
    },
    {
        "id": "iplan_sample_haifa_long_987_6543210",
        "type": RegulationType.LOCAL,
        "title": "תכנית 987-6543210 - תוספת בניה (חיפה)",
        "content": """
תכנית לדוגמה (מדמה נתוני iPlan) עם תוכן ארוך במיוחד כדי לייצר שונות באורכי מסמכים.

מספר תכנית: 987-6543210
רשות/עיר: חיפה
מחוז: חיפה
סוג תכנית: תכנית מפורטת
סטטוס: תכנית במוסדות התכנון

רקע ומטרות:
התכנית עוסקת בהתחדשות עירונית במתחם מעורב שימושים, לרבות חיזוק מבנים, תוספת קומות, הסדרת זכויות בניה,
והקצאת שטחים לצרכי ציבור. התכנית מבקשת לשפר את המרקם העירוני, להוסיף שטחים פתוחים, ולהסדיר תנועת רכב
והולכי רגל.

עקרונות תכנון:
1. שימור חזיתות היסטוריות במקטע הרחוב הראשי.
2. תוספת שימושים פעילים בקומת קרקע (מסחר, שירותים, קהילה).
3. שיפור רציפות שבילי הליכה והצללה.
4. ניהול נגר עילי והגדלת שטחי חלחול.

הוראות תכנוניות (תמצית):
- קווי בניין: מינימום 3.0 מ' מקדימה, 2.0 מ' בצדדים, 3.0 מ' מאחור; התאמות לפי נספח תנועה.
- גובה: עד 8 קומות מעל קומת קרקע; תוספות גג בכפוף להנחיות.
- חניה: שילוב חניה תת-קרקעית; אפשרות להפחתה סמוך לצירי תחבורה ציבורית; הקצאת חניה לנכים.
- שטחים ירוקים: 20% משטח המגרש כשטח פתוח/גינון; נטיעת עצים לפי תקן.

מסמכים נלווים:
- נספח בינוי, נספח תנועה, נספח ניקוז, נספח סביבתי.
        """.strip(),
        "summary": "דוגמה לתכנית עם פירוט ארוך ומגוון נושאים (כולל חניה)",
        "jurisdiction": "חיפה",
        "metadata": {
            "plan_number": "987-6543210",
            "plan_type": "תכנית מפורטת",
            "municipality": "חיפה",
            "municipality_name": "חיפה",
            "city": "חיפה",
            "district": "חיפה",
            "status": "תכנית במוסדות התכנון",
            "source": "sample_iplan",
        },
    },
]


def get_sample_regulations(source: str = "default") -> list:
    """Get sample regulations from specified source.
    
    Args:
        source: Data source identifier ("default", "israeli", etc.)
        
    Returns:
        List of regulation dictionaries
    """
    if source == "default":
        return DEFAULT_SAMPLE_REGULATIONS
    else:
        # Future: Add support for other sources
        # e.g., "israeli", "european", "custom"
        raise ValueError(f"Unknown regulation source: {source}")


def add_custom_regulations(regulations: list) -> None:
    """Add custom regulations to the available sources.
    
    This function can be extended in the future to support
    adding regulations from external files, APIs, or databases.
    
    Args:
        regulations: List of regulation dictionaries to add
    """
    # Future implementation: Support for custom regulation sources
    pass
