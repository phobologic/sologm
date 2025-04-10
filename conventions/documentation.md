# Documentation

## Docstrings
- Use Google-style format consistently
- Document purpose, parameters, return values, exceptions, and examples
- For unchanged overridden methods, use `"""See base class."""`

```python
def method(self, param: str) -> ReturnType:
    """Method description.
    
    Args:
        param: Parameter description.
        
    Returns:
        Description of return value.
        
    Raises:
        ErrorType: Error conditions.
    """
```

## Logging
- Use module-level logger: `logger = logging.getLogger(__name__)`
- Never use `print()` for debugging
- Log levels: DEBUG (development), INFO (confirmation), WARNING (unexpected), 
  ERROR (function failure), CRITICAL (application failure)
- Structure messages consistently:
  - Operations: "Starting operation_name for resource_type resource_id"
  - Errors: "Error in operation_name: details"
- Never log credentials
