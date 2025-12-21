from app.database import SessionLocal
from app.models import Provider
from app.utils.encryption import decrypt_credentials
from app.adapters import get_adapter

db = SessionLocal()
provider = db.query(Provider).filter(Provider.id == '6cd2ff67-3c06-406a-9b0b-adc583c82e16').first()
if provider:
    print(f'Testing Azure provider: {provider.name}')
    print(f'Provider ID: {provider.id}')
    print(f'\n=== Testing Connection ===')
    creds = decrypt_credentials(provider.credentials)
    print(f'Decrypted Credentials: {creds}')
    try:
        adapter = get_adapter('azure', creds)
        print(f'Adapter created: {adapter.credential}')
        result = adapter.test_connection()

        if result:
            print(f'\n✅ CONNECTION SUCCESSFUL!')
            print(f'\n=== Listing Instances ===')
            instances = adapter.list_instances()
            print(f'Found {len(instances)} instance(s)')
            if len(instances) > 0:
                print(f'\nInstances:')
                for inst in instances:
                    print(f'  • {inst["name"]}')
                    print(f'    Status: {inst["status"]}')
                    print(f'    Type: {inst["instance_type"]}')
                    print(f'    Region: {inst["region"]}')
                    print(f'    Cost: ${inst.get("monthly_cost", 0):.2f}/month')
                    print()
            else:
                print('  No instances found (this is normal if you have no VMs running)')
        else:
            print(f'\n❌ CONNECTION FAILED')
            print('Check the error messages above for details.')

    except Exception as e:
        print(f'\n❌ ERROR: {e}')
        import traceback
        traceback.print_exc()
db.close()
