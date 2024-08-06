import json


def test_create_button(admin_login):
    client = admin_login

    response = client.get(
        "/admin/user/new/?url=/admin/user/",
    )

    assert response.status_code == 200
    assert "Save and Add Another" in response.text
