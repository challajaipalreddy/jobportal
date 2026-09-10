from flask import Blueprint, jsonify, request
from app.models import Job, Company, Category

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/jobs')
def get_jobs():
    category_slug = request.args.get('category')
    company_slug = request.args.get('company')
    limit = request.args.get('limit', 10, type=int)

    query = Job.query.filter_by(status='Active')

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if company_slug:
        comp = Company.query.filter_by(slug=company_slug).first()
        if comp:
            query = query.filter_by(company_id=comp.id)

    jobs = query.order_by(Job.posted_date.desc()).limit(limit).all()

    data = []
    for j in jobs:
        data.append({
            'id': j.id,
            'title': j.title,
            'slug': j.slug,
            'company': j.company.name,
            'company_logo': j.company.logo,
            'location': j.location,
            'experience': j.experience,
            'job_type': j.job_type,
            'work_mode': j.work_mode,
            'salary': j.salary,
            'posted_date': j.posted_date.strftime('%Y-%m-%d'),
            'application_url': j.application_url,
            'youtube_video_url': j.youtube_video_url,
            'youtube_thumbnail': j.youtube_thumbnail
        })

    return jsonify({'success': True, 'count': len(data), 'jobs': data})

@api_bp.route('/jobs/<slug>')
def get_job_detail(slug):
    job = Job.query.filter_by(slug=slug).first()
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'}), 404

    return jsonify({
        'success': True,
        'job': {
            'id': job.id,
            'title': job.title,
            'slug': job.slug,
            'company': {
                'name': job.company.name,
                'slug': job.company.slug,
                'logo': job.company.logo,
                'website': job.company.website
            },
            'category': job.category.name if job.category else None,
            'job_type': job.job_type,
            'work_mode': job.work_mode,
            'location': job.location,
            'qualification': job.qualification,
            'experience': job.experience,
            'skills': job.skills,
            'salary': job.salary,
            'short_description': job.short_description,
            'description': job.description,
            'responsibilities': job.responsibilities,
            'eligibility': job.eligibility,
            'campus_analysis': job.campus_analysis,
            'who_can_apply': job.who_can_apply,
            'application_url': job.application_url,
            'posted_date': job.posted_date.isoformat(),
            'application_deadline': job.application_deadline.isoformat() if job.application_deadline else None,
            'youtube_video_url': job.youtube_video_url,
            'youtube_video_id': job.youtube_video_id,
            'views': job.views
        }
    })

@api_bp.route('/categories')
def get_categories():
    categories = Category.query.all()
    data = [{'id': c.id, 'name': c.name, 'slug': c.slug, 'icon': c.icon} for c in categories]
    return jsonify({'success': True, 'categories': data})

@api_bp.route('/companies')
def get_companies():
    companies = Company.query.all()
    data = [{'id': c.id, 'name': c.name, 'slug': c.slug, 'logo': c.logo, 'website': c.website} for c in companies]
    return jsonify({'success': True, 'companies': data})

# --- RAZORPAY STANDARD WEB CHECKOUT API ---
import razorpay
from flask import session
from app import db
from app.models import SiteSetting, PaymentSubmission

@api_bp.route('/razorpay/create-order', methods=['POST'])
def razorpay_create_order():
    try:
        key_id_setting = SiteSetting.query.filter_by(key='razorpay_key_id').first()
        key_secret_setting = SiteSetting.query.filter_by(key='razorpay_key_secret').first()
        price_setting = SiteSetting.query.filter_by(key='study_pass_price').first()

        key_id = key_id_setting.value.strip() if key_id_setting and key_id_setting.value else 'rzp_test_TaFAKzUooiq0cD'
        key_secret = key_secret_setting.value.strip() if key_secret_setting and key_secret_setting.value else 'pkBEw6iVbb2DGii8M4BdIW7Y'
        price = int(price_setting.value.strip()) if price_setting and price_setting.value else 99

        client = razorpay.Client(auth=(key_id, key_secret))
        order_data = {
            'amount': price * 100,  # Amount in paise (9900 = ₹99)
            'currency': 'INR',
            'payment_capture': '1'
        }
        order = client.order.create(data=order_data)
        return jsonify({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': key_id
        })
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@api_bp.route('/razorpay/verify-payment', methods=['POST'])
def razorpay_verify_payment():
    try:
        data = request.get_json() or request.form
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        email = data.get('email', 'customer@campustocareer.com')

        key_id_setting = SiteSetting.query.filter_by(key='razorpay_key_id').first()
        key_secret_setting = SiteSetting.query.filter_by(key='razorpay_key_secret').first()

        key_id = key_id_setting.value.strip() if key_id_setting and key_id_setting.value else 'rzp_test_TaFAKzUooiq0cD'
        key_secret = key_secret_setting.value.strip() if key_secret_setting and key_secret_setting.value else 'pkBEw6iVbb2DGii8M4BdIW7Y'

        client = razorpay.Client(auth=(key_id, key_secret))
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        client.utility.verify_payment_signature(params_dict)

        # Payment verified successfully! Grant lifetime PDF access to candidate
        session['pdf_access_unlocked'] = True

        # Save payment submission log in DB
        submission = PaymentSubmission(
            email=email,
            utr_ref=f"RZP-{razorpay_payment_id}",
            status='Approved',
            notes=f"Razorpay Order: {razorpay_order_id}"
        )
        db.session.add(submission)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Payment verified successfully! PDF Access granted.'})
    except Exception as err:
        return jsonify({'success': False, 'error': f"Signature verification failed: {str(err)}"}), 400

