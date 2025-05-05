import requests
from decouple import config
from datetime import datetime
import pytz

def publish_scheduled_blogs():
    print("Cron job running: Checking for blogs to publish...")

    # Airtable configuration
    
    airtable_api_key = config('AIRTABLE_API_KEY')
    airtable_base_id = config('AIRTABLE_BASE_ID')
    airtable_table_name = 'Blog Posts'
    airtable_url = f"https://api.airtable.com/v0/{airtable_base_id}/{airtable_table_name}"

    # WordPress configuration
    wordpress_url = config('WORDPRESS_URL')  
    wordpress_username = config('WORDPRESS_USERNAME')
    wordpress_password = config('WORDPRESS_PASSWORD')

    # Getting the current time in UTC
    current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)

    # Fetching the records from Airtable
    headers = {
        'Authorization': f'Bearer {airtable_api_key}',
        'Content-Type': 'application/json'
    }
    params = {
        'filterByFormula': 'AND({Status} = "Scheduled", {Publish Date} <= NOW())',
        'sort[0][field]': 'Publish Date',
        'sort[0][direction]': 'asc'
    }
    try:
        response = requests.get(airtable_url, headers=headers, params=params)
        response.raise_for_status()
        records = response.json().get('records', [])
        print(f"Found {len(records)} scheduled blogs to publish.")
    except Exception as e:
        print(f"Error fetching records from Airtable: {str(e)}")
        return

    # Processing each record
    for record in records:
        record_id = record['id']
        fields = record['fields']
        title = fields.get('Title', '')
        content = fields.get('Content', '')

        # Posting onto WordPress
        wp_headers = {
            'Content-Type': 'application/json',
        }
        wp_auth = (wordpress_username, wordpress_password)
        wp_data = {
            'title': title,
            'content': content,
            'status': 'publish'
        }
        try:
            wp_response = requests.post(wordpress_url, headers=wp_headers, auth=wp_auth, json=wp_data)
            wp_response.raise_for_status()
            wp_post_id = wp_response.json().get('id')
            print(f"Published to WordPress: {title}, Post ID: {wp_post_id}")
        except Exception as e:
            print(f"Error publishing to WordPress: {str(e)}")
            continue

        # Updating the Airtable record with WordPress Post ID and Status (draft/ scheduled and published)
        update_data = {
            'fields': {
                'WordPress Post ID': str(wp_post_id),
                'Status': 'Published'
            }
        }
        try:
            update_response = requests.patch(f"{airtable_url}/{record_id}", headers=headers, json=update_data)
            update_response.raise_for_status()
            print(f"Updated Airtable record {record_id}: Status set to Published, WordPress Post ID: {wp_post_id}")
        except Exception as e:
            print(f"Error updating Airtable record {record_id}: {str(e)}")
