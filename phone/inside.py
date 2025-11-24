# Simple in-memory storage for orders
ORDERS_DB = {"orders": {}, "next_id": 1}

# Course catalog (formerly DRUG_DB)
COURSE_DB = {
    "AI-Powered Maritime Cyber Security Course (MACSET)": {
        "name": "AI-Powered Maritime Cyber Security Course (MACSET)",
        "price": 315,
        "description": "The IMO’s guidelines and International Safety Management (ISM) Code demand not just compliance, but proven vigilance., Old protocols don’t cut it anymore., AI isn’t just helping the good guys., It’s fueling new attack vectors—from deepfakes able to impersonate port officials, to automated botnets targeting ECDIS, engine control, and OT networks., Ransomware has found ways to jump the air gap onto maritime systems., In 2023 alone, bulk carriers and ferries in both Europe and Asia lost millions of euros in downtime and regulatory fines., As vessels become smarter, their threat surfaces expand., Attackers can now exploit everything from smart sensors to integrated supply chain networks., What this really means is: It’s not enough to rely on yesterday’s knowledge., You need to understand the risks AI brings onboard, anticipate next-generation threats, and close compliance gaps before authorities or attackers spot them first.",
        "quantity": 1
    },
    "macset": {
        "name": "AI-Powered Maritime Cyber Security Course (MACSET)",
        "price": 315,
        "description": "The IMO’s guidelines and International Safety Management (ISM) Code demand not just compliance, but proven vigilance., Old protocols don’t cut it anymore., AI isn’t just helping the good guys., It’s fueling new attack vectors—from deepfakes able to impersonate port officials, to automated botnets targeting ECDIS, engine control, and OT networks., Ransomware has found ways to jump the air gap onto maritime systems., In 2023 alone, bulk carriers and ferries in both Europe and Asia lost millions of euros in downtime and regulatory fines., As vessels become smarter, their threat surfaces expand., Attackers can now exploit everything from smart sensors to integrated supply chain networks., What this really means is: It’s not enough to rely on yesterday’s knowledge., You need to understand the risks AI brings onboard, anticipate next-generation threats, and close compliance gaps before authorities or attackers spot them first.",
        "quantity": 1
    },
    "crowd management": {
        "name": "crowd management",
        "price": 150,
        "description": "Course is open to personnel who are designated on Muster lists to assist passengers in emergency situations. This course has been designed to meet the requirements of Regulations V/2, paragraph 4 of the STCW Convention and Code 1978 as amendedA certificate is issued by the college on the successful completion of the course on behalf of the Marshall Island Ship Registry",
        "quantity": 1
    },
    "crowd_management": {
        "name": "crowd management",
        "price": 150,
        "description": "Course is open to personnel who are designated on Muster lists to assist passengers in emergency situations. This course has been designed to meet the requirements of Regulations V/2, paragraph 4 of the STCW Convention and Code 1978 as amendedA certificate is issued by the college on the successful completion of the course on behalf of the Marshall Island Ship Registry",
        "quantity": 1
    },
    "cm": {
        "name": "crowd management",
        "price": 150,
        "description": "Course is open to personnel who are designated on Muster lists to assist passengers in emergency situations. This course has been designed to meet the requirements of Regulations V/2, paragraph 4 of the STCW Convention and Code 1978 as amendedA certificate is issued by the college on the successful completion of the course on behalf of the Marshall Island Ship Registry",
        "quantity": 1
    },
    "high_voltage": {
        "name": "high voltage",
        "price": 250,
        "description": "To give seafarers the essential education and training in high voltage installations to meet the Knowledge, Understanding and Profi ciency (KUP) requirements set out in the specific part of the following: Table A-III/1 Function: Electrical, electronic and control engineering at the operational level Competence: Operate electrical, electronic and control systems (part)",
        "quantity": 1
    }, 
    "high voltage": {
        "name": "high voltage",
        "price": 250,
        "description": "To give seafarers the essential education and training in high voltage installations to meet the Knowledge, Understanding and Profi ciency (KUP) requirements set out in the specific part of the following: Table A-III/1 Function: Electrical, electronic and control engineering at the operational level Competence: Operate electrical, electronic and control systems (part)",
        "quantity": 1
    },    
    "hvo": {
        "name": "high voltage",
        "price": 250,
        "description": "To give seafarers the essential education and training in high voltage installations to meet the Knowledge, Understanding and Profi ciency (KUP) requirements set out in the specific part of the following: Table A-III/1 Function: Electrical, electronic and control engineering at the operational level Competence: Operate electrical, electronic and control systems (part)",
        "quantity": 1
    },
    
}

def get_course_info(course_name):
    """Retrieve course information."""
    course = COURSE_DB.get(course_name.lower())
    if course:
        return {
            "name": course["name"],
            "description": course["description"],
            "price": course["price"],
            "quantity": course["quantity"]
        }
    return {"error": f"Course '{course_name}' not found"}


def place_order(customer_email, customer_phone, course_name):
    """Place an order for a course."""
    course = COURSE_DB.get(course_name.lower())
    if not course:
        return {"error": f"Course '{course_name}' not found"}

    order_id = ORDERS_DB["next_id"]
    ORDERS_DB["next_id"] += 1

    order = {
        "id": order_id,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        "course": course["name"],
        "quantity": course["quantity"],
        "total": course["price"],
        "status": "pending"
    }

    ORDERS_DB["orders"][order_id] = order

    return {
        "order_id": order_id,
        "message": (
            f"Order {order_id} placed: {course['quantity']} units of "
            f"{course['name']} for ${order['total']:.2f}"
        ),
        "total": order["total"],
        "quantity": course["quantity"]
    }


def lookup_order(order_id):
    """Look up an order by ID."""
    order = ORDERS_DB["orders"].get(int(order_id))
    if order:
        return {
            "order_id": order_id,
            "customer_email": order["customer_email"],
            "customer_phone": order["customer_phone"],
            "course": order["course"],
            "quantity": order["quantity"],
            "total": order["total"],
            "status": order["status"]
        }
    return {"error": f"Order {order_id} not found"}


# Function mapping for your AI agent / Twilio callback
FUNCTION_MAP = {
    'get_course_info': get_course_info,
    'place_order': place_order,
    'lookup_order': lookup_order
}
