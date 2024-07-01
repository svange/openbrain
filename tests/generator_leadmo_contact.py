from typing import Optional

from faker import Faker
from pydantic import BaseModel, Field

from openbrain.tools.models.model_leadmo_contact import LeadmoContactAdaptor


class LeadmoContact(BaseModel):
    """Internal ORM representing LeadmoContact."""

    contactId: Optional[str] = Field(default=None, description="The contact's id")
    locationId: str = Field(default=None, description="The agent's location ID in Lead Momentum")

    firstName: Optional[str] = Field(default=None, description="The contact's first name")
    lastName: Optional[str] = Field(default=None, description="The contact's last name")
    name: Optional[str] = Field(default=None, description="The contact's full name")
    dateOfBirth: Optional[str] = Field(default=None, description="The contact's date of birth")
    phone: Optional[str] = Field(default=None, description="The contact's phone number")
    email: Optional[str] = Field(default=None, description="The contact's email address")
    address1: Optional[str] = Field(default=None, description="The contact's address line 1")
    city: Optional[str] = Field(default=None, description="The contact's city")
    state: Optional[str] = Field(default=None, description="The contact's state")
    country: Optional[str] = Field(default=None, description="The contact's country")
    postalCode: Optional[str] = Field(default=None, description="The contact's postal code")
    companyName: Optional[str] = Field(default=None, description="The contact's company name")
    website: Optional[str] = Field(default=None, description="The contact's website")
    tags: Optional[list[str]] = Field(default=None, description="The contact's tags")
    customFields: Optional[dict[str, str]] = Field(default=None, description="The contact's custom fields")

    # Woxom Fields
    sessionId: Optional[str] = Field(default=None, description="The session_id associated with this contact")
#
fake = Faker()

fake_medication_list = [
    "Aspirin",
    "Ibuprofen",
    "Acetaminophen",
    "Metformin",
    "Atorvastatin",
    "Amlodipine",
    "Simvastatin",
    "Omeprazole",
    "Losartan",
    "Albuterol",
    "Gabapentin",
    "Hydrochlorothiazide",
    "Zolpidem",
    "Citalopram",
    "Meloxicam",
    "Fluoxetine",
    "Trazodone",
    "Sertraline",
    "Warfarin",
    "Clonazepam",
]


def generate_leadmo_contact(try_to_break_shit: bool = False, contact_id: str = None, location_id: str = None):
    firstName = fake.first_name()
    middleName = fake.first_name()
    lastName = fake.last_name()
    meds = [fake.random_element(fake_medication_list) for _ in range(fake.random_int(min=1, max=10))]
    meds_str = ', '.join(meds)
    leadmo_contact_dict = {
        'contactId': contact_id,
        'locationId': location_id,
        'firstName': firstName,
        'lastName': lastName,
        'middleName': middleName,
        'name': " ".join([firstName, middleName, lastName]),
        'dateOfBirth': "April 1, 1969",  # TODO: fake this up,
        'phone': fake.phone_number(),
        'email': fake.email(),
        'address1': fake.address(),
        'city': fake.city(),
        'state': fake.state(),
        'country': "US",
        'postalCode': fake.postcode(),
        'companyName': "Fake Company",
        'website': "http://www.woxomai.com",
        'customFields': {
            'medications': meds_str
        },
        'tags': ["woxom_ai", "test"]
    }

    if contact_id:
        leadmo_contact_dict['contactId'] = contact_id

    if location_id:
        leadmo_contact_dict['locationId'] = location_id

    leadmo_contact = LeadmoContact(**leadmo_contact_dict).model_dump()

    return leadmo_contact

def generate_ai_leadmo_contact(try_to_break_shit: bool = False):
    firstName = fake.first_name()
    middleName = fake.first_name()
    lastName = fake.last_name()
    meds = [fake.random_element(fake_medication_list) for _ in range(fake.random_int(min=1, max=10))]

    # current_medications
    leadmo_contact_dict = {
        'firstName': firstName,
        'lastName': lastName,
        'middleName': middleName,
        'name': " ".join([firstName, middleName, lastName]),
        'dateOfBirth': "April 1, 1969",  # TODO: fake this up,
        'phone': fake.phone_number(),
        'email': fake.email(),
        'address1': fake.address(),
        'city': fake.city(),
        'state': fake.state(),
        'country': "US",
        'postalCode': fake.postcode(),
        'companyName': "Fake Company",
        'website': "http://www.woxomai.com",
        'current_medications': meds
    }

    leadmo_contact = LeadmoContactAdaptor(**leadmo_contact_dict).model_dump()

    return leadmo_contact
