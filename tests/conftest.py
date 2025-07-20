import os
import sys
import types
# Add project root to sys.path so ft8ctrl can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

# Stub dbutils to avoid missing dependencies
_dbutils = types.ModuleType('dbutils')
_dbutils.DBCommand = types.SimpleNamespace(INSERT=None, DELETE=None, STATUS=None)
_dbutils.DBInsert = lambda *args, **kwargs: None
_dbutils.Purge = lambda *args, **kwargs: None
_dbutils.create_db = lambda *args, **kwargs: None
_dbutils.get_band = lambda x: x
sys.modules['dbutils'] = _dbutils

# Stub wsjtx to avoid missing dependency
sys.modules['wsjtx'] = types.ModuleType('wsjtx')

# Initialize ft8ctrl.LOG to a valid logger to prevent AttributeError during tests
import logging
import ft8ctrl
ft8ctrl.LOG = logging.getLogger('ft8ctrl_test') 