"""Tests for model registry persistence."""
import json
import os
from pathlib import Path
import pytest
from llm_reasoner.models import ModelRegistry, ModelConfig

def test_model_persistence(tmp_path):
    """Test that models are correctly saved and loaded."""
    # Create a temporary config file path
    config_dir = tmp_path / ".llm_reasoner"
    config_file = config_dir / "models.json"
    
    # Mock the constants in the models module for this test
    import llm_reasoner.models
    original_dir = llm_reasoner.models.CONFIG_DIR
    original_file = llm_reasoner.models.CONFIG_FILE
    
    llm_reasoner.models.CONFIG_DIR = config_dir
    llm_reasoner.models.CONFIG_FILE = config_file
    
    try:
        # 1. Initialize registry and register a custom model
        registry = ModelRegistry()
        custom_name = "test-persist-model"
        registry.register_model(custom_name, "test-provider", 1234)
        
        # Verify it's in the current registry
        assert custom_name in registry.list_models()
        assert registry.get_model(custom_name).context_window == 1234
        
        # Verify the file was created
        assert config_file.exists()
        
        # 2. Create a new registry instance and verify the model is loaded
        new_registry = ModelRegistry()
        assert custom_name in new_registry.list_models()
        assert new_registry.get_model(custom_name).context_window == 1234
        assert new_registry.get_model(custom_name).provider == "test-provider"
        
        # 3. Test setting default persistence
        new_registry.set_default_model(custom_name)
        assert new_registry.get_default_model().name == custom_name
        
        # 4. Create another registry instance and verify default is preserved
        final_registry = ModelRegistry()
        assert final_registry.get_default_model().name == custom_name
        
    finally:
        # Restore original constants
        llm_reasoner.models.CONFIG_DIR = original_dir
        llm_reasoner.models.CONFIG_FILE = original_file

def test_corrupted_config_handling(tmp_path):
    """Test that corrupted config files are handled gracefully."""
    config_dir = tmp_path / ".llm_reasoner"
    config_file = config_dir / "models.json"
    
    import llm_reasoner.models
    original_dir = llm_reasoner.models.CONFIG_DIR
    original_file = llm_reasoner.models.CONFIG_FILE
    
    llm_reasoner.models.CONFIG_DIR = config_dir
    llm_reasoner.models.CONFIG_FILE = config_file
    
    try:
        # Create a corrupted JSON file
        config_dir.mkdir(parents=True)
        with open(config_file, 'w') as f:
            f.write("{ invalid json")
            
        # Registry should initialize with defaults without crashing
        registry = ModelRegistry()
        assert "gpt-3.5-turbo" in registry.list_models()
        
    finally:
        llm_reasoner.models.CONFIG_DIR = original_dir
        llm_reasoner.models.CONFIG_FILE = original_file
