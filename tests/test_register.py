import json

def test_create_new_customer(admin_login):
    client = admin_login

    response = client.get(
        "/admin/user/new/?url=/admin/user/",
    )

    data = {
        "username": "dev00012",
        "password": "password123",
        "password_confirm": "password123",
        "device": "dev00012",
        "active": True,
        "roles": ["customer"],
    }

    save_user_endpoint = "/admin/user/new"

    response = client.post(
        save_user_endpoint,
        data=json.dumps(data),
        content_type='application/json',
    )

    assert response.status_code == 308
