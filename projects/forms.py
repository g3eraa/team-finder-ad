from django import forms

from users.validators import validate_github_url

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")

    def clean_github_url(self):
        github_url = self.cleaned_data["github_url"]
        if github_url:
            validate_github_url(github_url)
        return github_url
