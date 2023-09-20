import ulid
from faker import Faker

from openbrain.orm.model_lead import Lead

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


def generate_lead(try_to_break_shit: bool = False):
    first_name = fake.first_name()
    middle_name = fake.middle_name()
    last_name = fake.last_name()
    full_name = ' '.join([first_name, middle_name, last_name])
    if try_to_break_shit:
        med_list = [fake.word() for _ in range(fake.random_int(min=0, max=100))]

    else:
        # three random elements from fake_medication_list
        med_list = [
            fake.random_element(fake_medication_list) for _ in range(fake.random_int(min=1, max=10))
        ]

    return Lead(
        client_id=fake.uuid4(),
        session_id=fake.uuid4(),
        # first_name=fake.first_name(),
        # middle_name=fake.first_name(),
        # last_name=fake.last_name(),
        full_name=full_name,
        state_of_residence=fake.state(),
        email_address=fake.email(),
        phone=fake.phone_number(),
        med_list=med_list,
        lead_id=str(ulid.ULID().to_uuid()),
    )
