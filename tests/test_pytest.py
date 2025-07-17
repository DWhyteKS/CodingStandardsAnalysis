import pytest
from app.app import app, allowedFile


@pytest.fixture
def client():
    """Create test client for Flask testing"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context(): 
            yield client


# Flask route tests
def test_homepage_loads(client):
    """Test that homepage loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'PowerShell Code Reviewer' in response.data


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    

def test_upload_no_file(client):
    """Test upload with no file returns error"""
    response = client.post('/upload', data={})
    assert response.status_code == 302  # Redirect back to form


# Function tests  
def test_allowed_file_ps1():
    """Test .ps1 files are allowed"""
    assert allowedFile('test.ps1') == True


def test_allowed_file_psm1():
    """Test .psm1 files are allowed"""
    assert allowedFile('test.psm1') == True


def test_allowed_file_txt_not_allowed():
    """Test .txt files are not allowed"""
    assert allowedFile('test.txt') == False


def test_allowed_file_no_extension():
    """Test files without extension are not allowed"""
    assert allowedFile('testfile') == False