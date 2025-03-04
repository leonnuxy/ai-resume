import pytest
import os
from app.utils.file_handling import save_uploaded_file, parse_uploaded_file, remove_uploaded_file
from werkzeug.datastructures import FileStorage

def test_save_uploaded_file(tmp_path):
    # Create a mock file
    mock_file = FileStorage(
        stream=open(__file__, 'rb'),
        filename='test.txt',
        content_type='text/plain'
    )
    
    # Test file saving
    filename, file_path = save_uploaded_file(mock_file)
    assert os.path.exists(file_path)
    assert filename == 'test.txt'
    
    # Cleanup
    remove_uploaded_file(file_path)