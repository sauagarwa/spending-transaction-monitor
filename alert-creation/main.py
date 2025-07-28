# Structure:
# - `FastAPI` backend for alert storage and querying
# - LLM-based rule parser for natural language rules

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from parse_alert_graph import app as parse_alert_graph
from generate_alert_graph import app as generate_alert_graph
from pydantic import BaseModel, field_validator
from typing import Optional, List, Union
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Transaction(BaseModel):
    user_id: str
    transaction_date: Union[datetime, str]
    credit_card_num: str
    amount: float
    currency: Optional[str] = "USD"
    description: Optional[str] = ""
    merchant_name: str
    merchant_category: Optional[str] = ""
    merchant_city: Optional[str] = ""
    merchant_state: Optional[str] = ""
    merchant_country: Optional[str] = "US"
    merchant_latitude: Optional[float] = 0.0
    merchant_longitude: Optional[float] = 0.0
    merchant_zipcode: Optional[int] = 0
    trans_num: str
    authorization_code: Optional[str] = ""
    reference_number: Optional[str] = ""
    first_name: str
    last_name: str
    
    @field_validator('transaction_date', mode='before')
    def parse_transaction_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        return v
    
    @field_validator('amount', mode='before')
    def parse_amount(cls, v):
        return float(v) if v is not None else 0.0
    
    @field_validator('merchant_latitude', 'merchant_longitude', mode='before')
    def parse_coordinates(cls, v):
        return float(v) if v is not None else 0.0
    
    @field_validator('merchant_zipcode', mode='before')
    def parse_zipcode(cls, v):
        return int(v) if v is not None else 0
    
    @field_validator('currency', 'description', 'merchant_category', 'merchant_city', 'merchant_state', 'merchant_country', 'authorization_code', 'reference_number', mode='before')
    def handle_none_strings(cls, v):
        # Convert None to empty string to use default values
        if v is None:
            return None  # Let Pydantic use the default value
        return v
    
    class Config:
        # Allow parsing from different field names
        allow_population_by_field_name = True
        # Convert string datetime to datetime object
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }



class Alert(BaseModel):
    user_id: str
    merchant: str
    type: str
    description: str
    severity: Optional[str] = "info"
    amount: Optional[float] = None
    triggered_at: Optional[datetime] = None

class Rule(BaseModel):
    rule: str

class ValidateRuleRequest(BaseModel):
    rule: str
    transaction: Transaction

class GenerateAlertRequest(BaseModel):
    rule: str
    transaction: Transaction
    

@app.post("/alert-rules/validate")
def validate_alert_rule(request: ValidateRuleRequest):
    """
    Validate an alert rule using the provided transaction.
    Returns the parsed rule structure and validation results.
    """
    print("Validating rule:", request.rule)
    print("Using transaction:", request.transaction.model_dump())
    
    # Convert Pydantic model to dict for processing
    transaction_dict = request.transaction.model_dump()

    try:
        parsed_rule = parse_nl_rule_with_llm(request.rule, transaction_dict)
        
        if parsed_rule:
            return {
                "status": "valid",
                "message": "Alert rule validated successfully",
                "parsed_rule": parsed_rule,
                "transaction_used": transaction_dict,
                "validation_timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "invalid", 
                "message": "Rule could not be parsed or validated",
                "error": "LLM could not parse rule structure"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Validation failed: {str(e)}",
            "error": str(e)
        }


def parse_nl_rule_with_llm(alert_text, transaction):
    try:
         # Run actual LangGraph app here (uncomment below if integrated)
        result = parse_alert_graph.invoke({
            "transaction": transaction,
            "alert_text": alert_text
        })
        print("===== result ======")
        print(result)
        print("===== end result ======")
        
        return result
    except Exception as e:
        print("LLM parsing error:", e)
        return None
 

@app.post("/alert-rules/generate")
def generate_alert(request: GenerateAlertRequest):
    """
    Generate an alert for a specific transaction using the provided rule.
    Returns a structured Alert object if the rule is triggered.
    """
    print("Generating alert for rule:", request.rule)
        
    # Convert Pydantic model to dict for processing
    transaction_dict = request.transaction.model_dump()
    print("Transaction:", transaction_dict)

    try:
        alert_result = generate_alert_with_llm(request.rule, transaction_dict)
        
        if alert_result and alert_result.get("should_trigger", False):
            # Create structured Alert object
            alert = Alert(
                     user_id=request.transaction.user_id,
                     merchant=request.transaction.merchant_name,
                     type=alert_result.get("alert_type", "CUSTOM"),
                     description=alert_result.get("message", "Alert triggered"),
                     severity=alert_result.get("severity", "info"),
                     amount=request.transaction.amount,
                     triggered_at=datetime.now()
                 )
                 
            return {
                     "status": "triggered",
                     "message": "Alert generated successfully",
                     "alert": alert.model_dump(),
                     "rule_evaluation": alert_result,
                     "transaction_id": request.transaction.trans_num
                 }
        else:
            return {
                "status": "not_triggered",
                "message": "Rule evaluated but alert not triggered",
                "rule_evaluation": alert_result,
                "transaction_id": request.transaction.trans_num
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Alert generation failed: {str(e)}",
            "error": str(e),
            "transaction_id": request.transaction.trans_num
        }
    

def generate_alert_with_llm(alert_text, transaction):
    try:
         # Run actual LangGraph app here (uncomment below if integrated)
        result = generate_alert_graph.invoke({
            "transaction": transaction,
            "alert_text": alert_text
        })
        print("===== result ======")
        print(result)
        print("===== end result ======")
        
        return result
    except Exception as e:
        print("LLM parsing error:", e)
        return None
