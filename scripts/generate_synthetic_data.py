#!/usr/bin/env python3
"""
Synthetic Healthcare Data Generator

Generates FHIR-compliant synthetic patient data for CoCo demonstration.
All data is entirely synthetic - no real PHI.

Usage:
    python scripts/generate_synthetic_data.py --patients 100 --output data/
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


# Synthetic data pools
FIRST_NAMES_MALE = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
]

FIRST_NAMES_FEMALE = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth", "Susan",
    "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Betty", "Margaret", "Sandra",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
]

CONDITIONS = [
    {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
    {"code": "I10", "display": "Essential (primary) hypertension"},
    {"code": "J44.9", "display": "Chronic obstructive pulmonary disease, unspecified"},
    {"code": "I50.9", "display": "Heart failure, unspecified"},
    {"code": "E78.5", "display": "Hyperlipidemia, unspecified"},
    {"code": "J45.909", "display": "Unspecified asthma, uncomplicated"},
    {"code": "K21.0", "display": "Gastro-esophageal reflux disease with esophagitis"},
    {"code": "M54.5", "display": "Low back pain"},
    {"code": "F32.9", "display": "Major depressive disorder, single episode, unspecified"},
    {"code": "F41.1", "display": "Generalized anxiety disorder"},
]

MEDICATIONS = [
    {"code": "860975", "display": "Metformin 1000 MG"},
    {"code": "197884", "display": "Lisinopril 10 MG"},
    {"code": "617314", "display": "Atorvastatin 20 MG"},
    {"code": "860974", "display": "Metformin 500 MG"},
    {"code": "197885", "display": "Lisinopril 20 MG"},
    {"code": "312961", "display": "Amlodipine 5 MG"},
    {"code": "855332", "display": "Omeprazole 20 MG"},
    {"code": "198188", "display": "Hydrochlorothiazide 25 MG"},
    {"code": "749785", "display": "Sertraline 50 MG"},
    {"code": "866924", "display": "Losartan 50 MG"},
]

PROCEDURES = [
    {"code": "99213", "display": "Office visit, established patient, level 3"},
    {"code": "99214", "display": "Office visit, established patient, level 4"},
    {"code": "99215", "display": "Office visit, established patient, level 5"},
    {"code": "45378", "display": "Colonoscopy, diagnostic"},
    {"code": "77067", "display": "Screening mammography, bilateral"},
    {"code": "36415", "display": "Collection of venous blood by venipuncture"},
    {"code": "71046", "display": "Chest X-ray, 2 views"},
    {"code": "93000", "display": "Electrocardiogram, routine, with interpretation"},
]

LAB_TESTS = [
    {"code": "4548-4", "display": "Hemoglobin A1c", "unit": "%", "range": (5.0, 12.0)},
    {"code": "2345-7", "display": "Glucose [Mass/volume] in Serum or Plasma", "unit": "mg/dL", "range": (70, 200)},
    {"code": "2160-0", "display": "Creatinine [Mass/volume] in Serum or Plasma", "unit": "mg/dL", "range": (0.6, 2.5)},
    {"code": "33914-3", "display": "Glomerular filtration rate/1.73 sq M.predicted", "unit": "mL/min", "range": (30, 120)},
    {"code": "2093-3", "display": "Cholesterol [Mass/volume] in Serum or Plasma", "unit": "mg/dL", "range": (120, 280)},
    {"code": "13457-7", "display": "LDL Cholesterol", "unit": "mg/dL", "range": (50, 200)},
    {"code": "2085-9", "display": "HDL Cholesterol", "unit": "mg/dL", "range": (30, 90)},
    {"code": "2571-8", "display": "Triglycerides", "unit": "mg/dL", "range": (50, 400)},
]

IMMUNIZATIONS = [
    {"code": "141", "display": "Influenza, seasonal, injectable"},
    {"code": "208", "display": "COVID-19, mRNA, LNP-S"},
    {"code": "33", "display": "Pneumococcal polysaccharide PPV23"},
    {"code": "121", "display": "Zoster vaccine, live"},
    {"code": "113", "display": "Td (adult), adsorbed"},
]


def generate_patient_id() -> str:
    """Generate a unique patient ID."""
    return f"P{uuid.uuid4().hex[:8].upper()}"


def generate_encounter_id() -> str:
    """Generate a unique encounter ID."""
    return f"E{uuid.uuid4().hex[:8].upper()}"


def random_date(start_year: int = 2020, end_year: int = 2024) -> datetime:
    """Generate a random date within range."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def generate_patient() -> dict[str, Any]:
    """Generate a synthetic patient resource."""
    gender = random.choice(["male", "female"])
    first_names = FIRST_NAMES_MALE if gender == "male" else FIRST_NAMES_FEMALE
    
    birth_year = random.randint(1940, 2000)
    birth_date = datetime(birth_year, random.randint(1, 12), random.randint(1, 28))
    
    patient_id = generate_patient_id()
    
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "identifier": [
            {
                "system": "urn:oid:2.16.840.1.113883.4.3.25",
                "value": patient_id
            }
        ],
        "active": True,
        "name": [
            {
                "use": "official",
                "family": random.choice(LAST_NAMES),
                "given": [random.choice(first_names)]
            }
        ],
        "gender": gender,
        "birthDate": birth_date.strftime("%Y-%m-%d"),
        "address": [
            {
                "use": "home",
                "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                "postalCode": f"{random.randint(10000, 99999)}",
                "country": "US"
            }
        ],
        "maritalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                    "code": random.choice(["M", "S", "D", "W"]),
                }
            ]
        },
        "communication": [
            {
                "language": {
                    "coding": [
                        {
                            "system": "urn:ietf:bcp:47",
                            "code": random.choice(["en", "es", "zh"])
                        }
                    ]
                }
            }
        ],
        "meta": {
            "lastUpdated": datetime.utcnow().isoformat() + "Z"
        }
    }


def generate_condition(patient_id: str) -> dict[str, Any]:
    """Generate a synthetic condition resource."""
    condition = random.choice(CONDITIONS)
    onset_date = random_date(2015, 2023)
    
    return {
        "resourceType": "Condition",
        "id": str(uuid.uuid4()),
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active"
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed"
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "encounter-diagnosis"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                    "code": condition["code"],
                    "display": condition["display"]
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "onsetDateTime": onset_date.strftime("%Y-%m-%d"),
        "recordedDate": onset_date.strftime("%Y-%m-%d")
    }


def generate_observation(patient_id: str) -> dict[str, Any]:
    """Generate a synthetic lab observation."""
    lab = random.choice(LAB_TESTS)
    value = round(random.uniform(lab["range"][0], lab["range"][1]), 1)
    obs_date = random_date(2023, 2024)
    
    return {
        "resourceType": "Observation",
        "id": str(uuid.uuid4()),
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": lab["code"],
                    "display": lab["display"]
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": obs_date.isoformat() + "Z",
        "valueQuantity": {
            "value": value,
            "unit": lab["unit"],
            "system": "http://unitsofmeasure.org"
        }
    }


def generate_medication_request(patient_id: str) -> dict[str, Any]:
    """Generate a synthetic medication request."""
    med = random.choice(MEDICATIONS)
    auth_date = random_date(2023, 2024)
    
    return {
        "resourceType": "MedicationRequest",
        "id": str(uuid.uuid4()),
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": med["code"],
                    "display": med["display"]
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "authoredOn": auth_date.isoformat() + "Z",
        "dosageInstruction": [
            {
                "text": f"Take {random.choice(['once', 'twice'])} daily",
                "timing": {
                    "repeat": {
                        "frequency": random.choice([1, 2]),
                        "period": 1,
                        "periodUnit": "d"
                    }
                }
            }
        ]
    }


def generate_immunization(patient_id: str) -> dict[str, Any]:
    """Generate a synthetic immunization record."""
    imm = random.choice(IMMUNIZATIONS)
    imm_date = random_date(2022, 2024)
    
    return {
        "resourceType": "Immunization",
        "id": str(uuid.uuid4()),
        "status": "completed",
        "vaccineCode": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": imm["code"],
                    "display": imm["display"]
                }
            ]
        },
        "patient": {
            "reference": f"Patient/{patient_id}"
        },
        "occurrenceDateTime": imm_date.isoformat() + "Z",
        "primarySource": True
    }


def generate_procedure(patient_id: str) -> dict[str, Any]:
    """Generate a synthetic procedure."""
    proc = random.choice(PROCEDURES)
    proc_date = random_date(2022, 2024)
    
    return {
        "resourceType": "Procedure",
        "id": str(uuid.uuid4()),
        "status": "completed",
        "code": {
            "coding": [
                {
                    "system": "http://www.ama-assn.org/go/cpt",
                    "code": proc["code"],
                    "display": proc["display"]
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "performedDateTime": proc_date.isoformat() + "Z"
    }


def generate_patient_bundle(num_patients: int = 100) -> dict[str, Any]:
    """Generate a FHIR Bundle with synthetic patient data."""
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "entry": []
    }
    
    for i in range(num_patients):
        # Generate patient
        patient = generate_patient()
        patient_id = patient["id"]
        
        bundle["entry"].append({
            "resource": patient,
            "fullUrl": f"urn:uuid:{patient_id}"
        })
        
        # Generate 2-5 conditions per patient
        for _ in range(random.randint(2, 5)):
            condition = generate_condition(patient_id)
            bundle["entry"].append({"resource": condition})
        
        # Generate 5-15 observations (labs) per patient
        for _ in range(random.randint(5, 15)):
            observation = generate_observation(patient_id)
            bundle["entry"].append({"resource": observation})
        
        # Generate 2-8 medications per patient
        for _ in range(random.randint(2, 8)):
            med_request = generate_medication_request(patient_id)
            bundle["entry"].append({"resource": med_request})
        
        # Generate 1-4 immunizations per patient
        for _ in range(random.randint(1, 4)):
            immunization = generate_immunization(patient_id)
            bundle["entry"].append({"resource": immunization})
        
        # Generate 2-6 procedures per patient
        for _ in range(random.randint(2, 6)):
            procedure = generate_procedure(patient_id)
            bundle["entry"].append({"resource": procedure})
        
        if (i + 1) % 10 == 0:
            print(f"Generated {i + 1}/{num_patients} patients...")
    
    return bundle


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic healthcare data")
    parser.add_argument("--patients", type=int, default=100, help="Number of patients to generate")
    parser.add_argument("--output", type=str, default="data/", help="Output directory")
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {args.patients} synthetic patients...")
    bundle = generate_patient_bundle(args.patients)
    
    # Save as FHIR Bundle
    bundle_path = output_dir / "synthetic_patients.json"
    with open(bundle_path, "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"Saved FHIR Bundle to {bundle_path}")
    
    # Save patient list for easy reference
    patients = [
        entry["resource"] for entry in bundle["entry"]
        if entry["resource"]["resourceType"] == "Patient"
    ]
    patients_path = output_dir / "patient_list.json"
    with open(patients_path, "w") as f:
        json.dump(patients, f, indent=2)
    print(f"Saved patient list to {patients_path}")
    
    # Generate summary
    summary = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_patients": len(patients),
        "total_resources": len(bundle["entry"]),
        "resource_counts": {}
    }
    
    for entry in bundle["entry"]:
        rt = entry["resource"]["resourceType"]
        summary["resource_counts"][rt] = summary["resource_counts"].get(rt, 0) + 1
    
    summary_path = output_dir / "generation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {summary_path}")
    
    print("\nGeneration complete!")
    print(f"  Total patients: {summary['total_patients']}")
    print(f"  Total resources: {summary['total_resources']}")
    for rt, count in summary["resource_counts"].items():
        print(f"    {rt}: {count}")


if __name__ == "__main__":
    main()
