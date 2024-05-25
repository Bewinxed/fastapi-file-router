![00034-3220091456](https://github.com/Bewinxed/fastapi-file-router/assets/9145989/760cff2c-dffb-4e08-9617-5de26c861a05)

# FastAPI File-Based Router 🚀

## Motivation

Sveltekit ruined me 🤓! I made this package because:

> 1. File-based routing is the bees knees.
> 2. I like to watch the world burn.
> 3. It's just easier, bro.

This Python module dynamically loads FastAPI routes from a specified directory structure. It is designed to streamline the integration of API routes into a FastAPI app, making it easy to manage large applications with many endpoints.

## HOW TO USE

You can import routes and API Routers as usual, but whenever you want, if you structure your endpoints like below, it will loop over the directory and put all the routes correctly.

### Example

```
📁 project_root/
├ 📁 routes/  # This folder is set as the directory in the load_routes function
│ ├ 📄 route.py  # Translates to /api (base route of the directory)
│   │
│ ├ 📁 users/
│   │ ├ 📄 route.py  # /api/users
│   │ ├ 📄 [user_id].py  # /api/users/{user_id}
│   │ └ 📄 profile.py  # /api/users/profile
│   │
│ ├ 📁 products/
│   │ ├ 📄 route.py  # /api/products
│   │ └ 📁 [product_id]/
│   │  ├ 📄 route.py  # /api/products/{product_id}
│   │  └ 📄 reviews.py  # /api/products/{product_id}/reviews
│   │
│ └ 📁 settings/
│  ├ 📄 route.py  # /api/settings
│  └ 📁 notifications/
│      ├ 📄 route.py  # /api/settings/notifications
│      └ 📄 email.py  # /api/settings/notifications/email
├ 📁 templates/
│ └ 📄 home.html  # Not relevant to FastAPI routes
└ 📄 main.py  # Where you set up your FastAPI app and call load_routes
```

## Installation

Clone this repository or copy the script into your project directory:

```bash
pip install fastapi-file-router
```

## Usage

```python
from fastapi import FastAPI
from fastapi_file_router import load_routes

app = FastAPI()

load_routes(server, "routes", verbose=True)

# Optional
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
    )

```

# Logging

Enable verbose logging to get detailed output during the route loading process, which can be helpful for debugging:

```
load_routes(app, Path("./routes"), verbose=True)
```

# Contributing

Contributions are welcome! Please fork the repository and open a pull request with your features or fixes.

# License

Don't be a bozo.
