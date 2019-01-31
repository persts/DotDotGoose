# Schema

The pnt file is a JSON object with an array and four dictionaries. 
``` json
{
    "classes": [str],
    "points": {
        "image_name": {
            "class_name": [point]
        }
    },
    "colors": {
        "class_name": [ int, int, int]
    },
    "metadata": {
        "survey_id": str,
        "coordinates": {
            "image_name": {
                "x": str,
                "y": str
            }
        }
    },
    "custom_fields": {
        "fields": [field_def],
        "data": {
            "filed_name": {
                "image_name": str
            }
        }
    }
}

point: {
    "x": float,
    "y": float
}

field_def: [ str, str]
```
