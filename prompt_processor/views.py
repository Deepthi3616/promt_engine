# prompt_processor/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json

from .models import PromptConversion, ISTVONTemplate
from .services import ISTVONMapper
from .validators import ISTVONValidator

def index(request):
    """Main page with prompt input form"""
    recent_conversions = PromptConversion.objects.filter(success_flag=True)[:5]
    templates = ISTVONTemplate.objects.filter(is_active=True)[:5]
    
    context = {
        'recent_conversions': recent_conversions,
        'templates': templates,
    }
    return render(request, 'prompt_processor/index.html', context)

def convert_prompt(request):
    """Convert natural language prompt to ISTVON"""
    if request.method == 'POST':
        original_prompt = request.POST.get('prompt', '').strip()
        
        if not original_prompt:
            messages.error(request, 'Please enter a prompt to convert.')
            return redirect('index')
        
        try:
            # Convert using mapping logic
            mapper = ISTVONMapper()
            istvon_json = mapper.convert_to_istvon(original_prompt)
            
            # Validate the result
            validator = ISTVONValidator()
            is_valid, error_message = validator.validate_istvon(istvon_json)
            
            if not is_valid:
                raise ValueError(f"Generated invalid ISTVON: {error_message}")
            
            # Save to database
            conversion = PromptConversion.objects.create(
                original_prompt=original_prompt,
                istvon_json=istvon_json,
                success_flag=True
            )
            
            messages.success(request, 'Prompt converted successfully!')
            return redirect('review', conversion_id=conversion.id)
            
        except Exception as e:
            # Log error
            PromptConversion.objects.create(
                original_prompt=original_prompt,
                istvon_json={},
                success_flag=False,
                error_message=str(e)
            )
            messages.error(request, f'Conversion failed: {str(e)}')
            return redirect('index')
    
    return redirect('index')

def review(request, conversion_id):
    """Review page showing original vs ISTVON"""
    conversion = get_object_or_404(PromptConversion, id=conversion_id)
    
    # Format JSON for display
    istvon_pretty = json.dumps(conversion.istvon_json, indent=2) if conversion.istvon_json else "{}"
    
    # Get validation suggestions if available
    suggestions = {}
    if conversion.success_flag and conversion.istvon_json:
        validator = ISTVONValidator()
        suggestions = validator.get_validation_suggestions(conversion.istvon_json)
    
    context = {
        'conversion': conversion,
        'istvon_pretty': istvon_pretty,
        'suggestions': suggestions,
    }
    return render(request, 'prompt_processor/review.html', context)

def save_feedback(request, conversion_id):
    """Save user feedback on a conversion"""
    if request.method == 'POST':
        conversion = get_object_or_404(PromptConversion, id=conversion_id)
        
        rating = request.POST.get('rating')
        feedback = request.POST.get('feedback', '')
        
        if rating:
            conversion.user_rating = int(rating)
        if feedback:
            conversion.user_feedback = feedback
        
        conversion.save()
        messages.success(request, 'Thank you for your feedback!')
        
        return redirect('review', conversion_id=conversion_id)
    
    return redirect('index')

def history(request):
    """Show conversion history"""
    conversions = PromptConversion.objects.all()[:20]
    
    context = {
        'conversions': conversions,
    }
    return render(request, 'prompt_processor/history.html', context)

def api_convert(request):
    """API endpoint for programmatic access"""
    if request.method == 'POST':
        try:
            # Handle both form data and JSON
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                prompt = data.get('prompt', '')
            else:
                prompt = request.POST.get('prompt', '')
            
            if not prompt:
                return JsonResponse({
                    'success': False,
                    'error': 'No prompt provided'
                }, status=400)
            
            # Convert prompt
            mapper = ISTVONMapper()
            istvon_json = mapper.convert_to_istvon(prompt)
            
            # Validate
            validator = ISTVONValidator()
            is_valid, error_message = validator.validate_istvon(istvon_json)
            
            if not is_valid:
                return JsonResponse({
                    'success': False,
                    'error': f'Validation failed: {error_message}'
                }, status=500)
            
            # Save to database
            conversion = PromptConversion.objects.create(
                original_prompt=prompt,
                istvon_json=istvon_json,
                success_flag=True
            )
            
            return JsonResponse({
                'success': True,
                'conversion_id': conversion.id,
                'original_prompt': prompt,
                'istvon_json': istvon_json
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'error': 'POST method required'
    }, status=405)