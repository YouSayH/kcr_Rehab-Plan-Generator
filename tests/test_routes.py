def test_login_page_loads(client):
    """ログインページが正常に開くか（GETリクエスト）"""
    response = client.get('/login')
    assert response.status_code == 200

    # 【修正】レスポンスのバイト列をUTF-8でデコードしてから検索
    html_content = response.data.decode("utf-8")
    assert "ログイン" in html_content

def test_index_redirects_unauthorized(client):
    """未ログインでトップページに行くとログインページに飛ばされるか"""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert "/login" in response.request.path
