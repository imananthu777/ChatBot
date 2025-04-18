from flask import Flask, render_template, request, jsonify
from functools import wraps
import re
from datetime import datetime
from waitress import serve

app = Flask(__name__, static_folder='static', template_folder='templates')

# Simulated customer database with extended information
VALID_CUSTOMERS = {
    'POL123456': {
        'mobile': '9876543210',
        'name': 'John Doe',
        'email': 'john.doe@email.com',
        'address': '123 Main St, City',
        'kyc_status': 'Verified',
        'kyc_last_updated': '2024-12-01',
        'nominee': {
            'name': 'Sarah Doe',
            'relation': 'Spouse',
            'share': '100%'
        },
        'bank_details': {
            'bank_name': 'HDFC Bank',
            'account_no': 'XXXX1234',
            'ifsc': 'HDFC0001234'
        },
        'policy_type': 'ULIP',
        'policy_details': {
            'issue_date': '2020-04-15',
            'maturity_date': '2030-04-15',
            'premium_amount': 25000,
            'premium_frequency': 'Annual',
            'next_due_date': '2025-04-15'
        },
        'premium_history': [
            {'date': '2025-04-01', 'amount': 25000, 'receipt_no': 'REC12345'},
            {'date': '2024-04-01', 'amount': 25000, 'receipt_no': 'REC12344'},
            {'date': '2023-04-01', 'amount': 25000, 'receipt_no': 'REC12343'},
            {'date': '2022-04-01', 'amount': 25000, 'receipt_no': 'REC12342'},
            {'date': '2021-04-01', 'amount': 25000, 'receipt_no': 'REC12341'}
        ],
        'claim_history': [],
        'is_nri': False,
        'validated': False
    },
    'POL654321': {
        'mobile': '1234567890',
        'name': 'Jane Smith',
        'email': 'jane.smith@email.com',
        'address': '456 Elm St, Town',
        'kyc_status': 'Pending',
        'kyc_last_updated': '2023-11-15',
        'nominee': {
            'name': 'Tom Smith',
            'relation': 'Son',
            'share': '100%'
        },
        'bank_details': {
            'bank_name': 'ICICI Bank',
            'account_no': 'XXXX5678',
            'ifsc': 'ICIC0005678'
        },
        'policy_type': 'Traditional',
        'policy_details': {
            'issue_date': '2018-06-10',
            'maturity_date': '2028-06-10',
            'premium_amount': 15000,
            'premium_frequency': 'Annual',
            'next_due_date': '2025-06-10'
        },
        'premium_history': [
            {'date': '2024-06-01', 'amount': 15000, 'receipt_no': 'REC54321'},
            {'date': '2023-06-01', 'amount': 15000, 'receipt_no': 'REC54320'},
            {'date': '2022-06-01', 'amount': 15000, 'receipt_no': 'REC54319'}
        ],
        'claim_history': [],
        'is_nri': False,
        'validated': False
    }
}

def is_valid_policy_number(policy_number):
    return policy_number in VALID_CUSTOMERS

def is_valid_mobile(mobile):
    return any(customer['mobile'] == mobile for customer in VALID_CUSTOMERS.values())

def get_customer_data(identifier):
    if identifier in VALID_CUSTOMERS:
        return VALID_CUSTOMERS[identifier]
    for policy_number, data in VALID_CUSTOMERS.items():
        if data['mobile'] == identifier:
            return data
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    message = request.json.get('message', '').strip()
    session_data = request.json.get('sessionData', {})
    is_validated = session_data.get('isValidated', False)
    current_policy = session_data.get('policy_number', '')
    
    if not is_validated:
        if message.startswith('POL') or message.isdigit():
            is_policy = message.startswith('POL')
            is_valid = is_valid_policy_number(message) if is_policy else is_valid_mobile(message)
            
            if is_valid:
                customer_data = get_customer_data(message)
                session_data['policy_number'] = message if is_policy else next(
                    pol for pol, data in VALID_CUSTOMERS.items() 
                    if data['mobile'] == message
                )
                return jsonify({
                    'response': {
                        'message': f'Welcome back, {customer_data["name"]}! How may I assist you today?',
                        'options': [
                            'Policy Servicing',
                            'Premium Payment',
                            'Claims'
                        ],
                        'isValidated': True,
                        'sessionData': session_data
                    }
                })
            else:
                return jsonify({
                    'response': {
                        'message': 'I couldn\'t verify those credentials. Please enter a valid policy number (starting with POL) or mobile number.',
                        'isValidated': False
                    }
                })
        else:
            return jsonify({
                'response': {
                    'message': 'To help you better, I\'ll need either your policy number (starting with POL) or mobile number.',
                    'isValidated': False
                }
            })
    
    message = message.lower()
    customer_data = get_customer_data(current_policy)
    
    # Policy Servicing Menu
    if message in ['policy servicing', '1']:
        response = {
            'message': 'Please select from these Policy Servicing options:',
            'options': [
                '📝 Update Policy Information',
                '📄 Download Policy Documents',
                'Back to main menu'
            ]
        }
    
    # Update Policy Information sub-menu
    elif 'update policy information' in message:
        response = {
            'message': 'What information would you like to update?',
            'options': [
                f'🔍 Update KYC Information - Last updated: {customer_data["kyc_last_updated"]}',
                f'👤 Update Name - Current: {customer_data["name"]}',
                f'📧 Update Email - Current: {customer_data["email"]}',
                f'📱 Update Mobile - Current: {customer_data["mobile"]}',
                f'🏠 Update Address - Current: {customer_data["address"]}',
                f'👥 Update Nominee - Current: {customer_data["nominee"]["name"]}',
                f'🏦 Update Bank Account - Current: {customer_data["bank_details"]["account_no"]}',
                'Back to Policy Servicing'
            ]
        }
    
    # Download Policy Documents sub-menu
    elif 'download policy documents' in message:
        options = [
            '📄 E-Policy Document',
            '💰 Premium Paid Certificate',
            '🧾 Renewal Receipt'
        ]
        if customer_data['policy_type'] == 'ULIP':
            options.append('📊 Account Statement (ULIP)')
        options.append('Back to Policy Servicing')
        response = {
            'message': 'Select a document to download:',
            'options': options
        }
    
    # Premium Payment Menu
    elif message in ['premium payment', '2']:
        next_premium = customer_data['policy_details']['premium_amount']
        next_due = customer_data['policy_details']['next_due_date']
        response = {
            'message': 'Premium Payment Options:',
            'options': [
                f'💳 Pay your Premium - Next due: ₹{next_premium:,} on {next_due}',
                '📊 Last Premium Paid Details',
                '📅 Premium Schedule (PPT)',
                'Back to main menu'
            ]
        }
    
    # Claims Menu
    elif message in ['claims', '3']:
        response = {
            'message': 'Claims Services:',
            'options': [
                '📝 Initiate claim process',
                '🔍 Track claim document',
                'Back to main menu'
            ]
        }
    
    # Handle specific actions
    elif 'kyc' in message:
        response = {
            'message': 'Your KYC was last updated on ' + customer_data['kyc_last_updated'],
            'options': [
                '✨ Update KYC now',
                '📝 Self-declare no changes',
                'Back to Policy Information'
            ]
        }
    
    elif 'update email' in message:
        response = {
            'message': f'Current email: {customer_data["email"]}',
            'options': [
                '✏️ Enter new email address',
                '❌ Cancel email update',
                'Back to Policy Information'
            ]
        }
    
    elif 'premium paid certificate' in message:
        response = {
            'message': 'Select Financial Year:',
            'options': [
                '📄 FY 2024-25',
                '📄 FY 2023-24',
                '📄 FY 2022-23',
                'Back to Documents'
            ]
        }
    
    elif 'last premium paid' in message:
        history = customer_data['premium_history'][:5]
        options = [
            f'📅 {item["date"]}: ₹{item["amount"]:,} (Receipt: {item["receipt_no"]})'
            for item in history
        ]
        options.append('Back to Premium Payment')
        response = {
            'message': 'Last 5 premium payments:',
            'options': options
        }
    
    elif 'premium schedule' in message:
        policy = customer_data['policy_details']
        response = {
            'message': 'Premium Schedule Details:',
            'options': [
                f'📅 Policy Issue Date: {policy["issue_date"]}',
                f'💰 Premium Amount: ₹{policy["premium_amount"]:,}',
                f'🔄 Frequency: {policy["premium_frequency"]}',
                f'📅 Next Due Date: {policy["next_due_date"]}',
                f'🎯 Maturity Date: {policy["maturity_date"]}',
                'Back to Premium Payment'
            ]
        }
    
    elif 'initiate claim' in message:
        response = {
            'message': 'Required documents for claim:',
            'options': [
                '📄 Original Policy Document',
                '📝 Filled Claim Form',
                '🆔 ID Proof of Nominee',
                '🏦 Bank Account Details',
                '📱 Start claim process',
                'Back to Claims'
            ]
        }
    
    elif 'track claim' in message:
        if customer_data['claim_history']:
            claims = customer_data['claim_history']
            options = [f'Claim #{claim["id"]}: {claim["status"]}' for claim in claims]
        else:
            options = ['No active claims found']
        options.append('Back to Claims')
        response = {
            'message': 'Claim Status:',
            'options': options
        }
    
    elif 'e-policy document' in message:
        # Generate a dummy PDF for the E-Policy Document
        from flask import send_file
        import io
        from reportlab.pdfgen import canvas

        pdf_buffer = io.BytesIO()
        pdf = canvas.Canvas(pdf_buffer)
        pdf.drawString(100, 750, "E-Policy Document")
        pdf.drawString(100, 730, f"Policy Number: {current_policy}")
        pdf.drawString(100, 710, f"Policy Holder: {customer_data['name']}")
        pdf.drawString(100, 690, "This is a dummy E-Policy Document.")
        pdf.save()
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='e_policy_document.pdf')
    
    elif message == 'back to main menu':
        response = {
            'message': 'What would you like help with?',
            'options': [
                'Policy Servicing',
                'Premium Payment',
                'Claims'
            ]
        }
    elif 'back to policy servicing' in message:
        response = {
            'message': 'Please select from these Policy Servicing options:',
            'options': [
                '📝 Update Policy Information',
                '📄 Download Policy Documents',
                'Back to main menu'
            ]
        }
    else:
        response = {
            'message': 'Please select from these options:',
            'options': [
                'Policy Servicing',
                'Premium Payment',
                'Claims'
            ]
        }
    
    response['isValidated'] = True
    response['sessionData'] = session_data
    return jsonify({'response': response})

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=3000)