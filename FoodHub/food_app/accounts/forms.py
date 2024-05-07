from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


class SignUpForm(UserCreationForm):
	class Meta:
		model = get_user_model()
		fields = ("username", "password1", "password2", "age", "gender")
		labels = {
            'username': 'اسم المستخدم',
	    	'password1': 'كلمة المرور',
		    'password2': 'تأكيد كلمة المرور',
		    'age': 'العمر',
		    'gender': 'الجنس',
        }
