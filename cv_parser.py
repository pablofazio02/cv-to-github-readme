import PyPDF2
import re
import requests
from typing import Optional, Dict, List


class CVParser:
    """Parser for extracting information from CV PDFs, specifically GitHub usernames"""
    
    def __init__(self):
        self.github_patterns = [
            r'github\.com/([a-zA-Z0-9_-]+)',  # Full GitHub URL
            r'@([a-zA-Z0-9_-]+)',             # @username format
            r'GitHub:\s*([a-zA-Z0-9_-]+)',    # GitHub: username
            r'Github:\s*([a-zA-Z0-9_-]+)',    # Github: username (alternative spelling)
            r'GitHub\s+profile:\s*([a-zA-Z0-9_-]+)',  # GitHub profile: username
            r'Github\s+profile:\s*([a-zA-Z0-9_-]+)',  # Github profile: username
            r'(?:my\s+)?GitHub:\s*([a-zA-Z0-9_-]+)',  # My GitHub: username
            r'(?:my\s+)?Github:\s*([a-zA-Z0-9_-]+)',  # My Github: username
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def find_github_username(self, text: str) -> Optional[str]:
        """Find GitHub username in the text using various patterns"""        
        # Try each pattern to find GitHub username
        for pattern in self.github_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first match, cleaned
                username = matches[0].strip()
                # Basic validation - GitHub usernames can't be longer than 39 chars
                # and must contain only alphanumeric, hyphens, or underscores
                if len(username) <= 39 and re.match(r'^[a-zA-Z0-9_-]+$', username):
                    return username
        
        return None
    
    def verify_github_user(self, username: str) -> bool:
        """Verify if the GitHub user exists"""
        if not username:
            return False
            
        try:
            response = requests.get(f'https://api.github.com/users/{username}', timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error verifying GitHub user {username}: {e}")
            return False
    
    def extract_github_info(self, pdf_path: str) -> Dict[str, Optional[str]]:
        """Extract and verify GitHub information from CV"""
        result = {
            'username': None,
            'verified': False,
            'text_extracted': False
        }
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return result
        
        result['text_extracted'] = True
        
        # Find GitHub username
        username = self.find_github_username(text)
        if not username:
            return result
        
        result['username'] = username
        
        # Verify the user exists
        result['verified'] = self.verify_github_user(username)
        
        return result


class ReadmeGenerator:
    """Generator for creating personalized README files"""
    
    def __init__(self, template_path: str = "example_README.md"):
        self.template_path = template_path
    
    def load_template(self) -> str:
        """Load the README template"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading template: {e}")
            return ""
    
    def replace_github_username(self, content: str, old_username: str, new_username: str) -> str:
        """Replace GitHub username in the README content"""
        # Replace all occurrences of the old username with the new one
        # This handles github.com URLs, GitHub stats URLs, and other references
        # But avoids replacing email addresses
        patterns_to_replace = [
            # GitHub URLs
            (f'github.com/{old_username}', f'github.com/{new_username}'),
            # GitHub stats API parameters
            (f'username={old_username}&', f'username={new_username}&'),
            (f'username={old_username}', f'username={new_username}'),
            (f'user={old_username}&', f'user={new_username}&'),
            (f'user={old_username}', f'user={new_username}'),
            # GitHub stats URLs at the end of lines
            (f'/{old_username}"', f'/{new_username}"'),
        ]
        
        updated_content = content
        for old_pattern, new_pattern in patterns_to_replace:
            updated_content = updated_content.replace(old_pattern, new_pattern)
        
        return updated_content
    
    def generate_readme(self, github_username: str, output_path: str = "generated_README.md") -> bool:
        """Generate personalized README with the correct GitHub username"""
        template_content = self.load_template()
        if not template_content:
            return False
        
        # Replace the default username (pablofazio02) with the extracted one
        updated_content = self.replace_github_username(
            template_content, 
            "pablofazio02",  # Default username in template
            github_username
        )
        
        # Write the generated README
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
            return True
        except Exception as e:
            print(f"Error writing README: {e}")
            return False