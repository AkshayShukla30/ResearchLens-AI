import pymupdf as fitz
import pytest
from fastapi.testclient import TestClient

import main


def make_pdf(pages):
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_textbox(fitz.Rect(50, 50, 550, 780), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture()
def client():
    main._store = None
    main._service = None
    c = TestClient(main.app)
    c.delete("/api/documents")
    return c


def upload(client, name, pages, **form):
    return client.post("/api/documents", files=[("files", (name, make_pdf(pages), "application/pdf"))], data=form)


PAPER_A = ["Transformers use self attention for sequence modelling. " * 15,
           "Experiments show BLEU improvements on translation benchmarks. " * 15]
PAPER_B = ["Convolutional networks extract spatial features from images. " * 15,
           "ResNet residual connections enable very deep image classifiers. " * 15]


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_upload_list_delete(client):
    r = upload(client, "a.pdf", PAPER_A)
    assert r.status_code == 200, r.text
    doc = r.json()["uploaded"][0]
    assert doc["pages"] == 2 and doc["chunks"] >= 2
    assert len(client.get("/api/documents").json()) == 1
    assert upload(client, "a.pdf", PAPER_A).status_code == 400  # duplicate
    assert client.delete(f"/api/documents/{doc['doc_id']}").status_code == 200
    assert client.get("/api/documents").json() == []


def test_reject_non_pdf(client):
    r = client.post("/api/documents", files=[("files", ("x.txt", b"hello", "text/plain"))])
    assert r.status_code == 400


def test_ask_search_with_citations(client):
    upload(client, "a.pdf", PAPER_A)
    upload(client, "b.pdf", PAPER_B)
    r = client.post("/api/ask", json={"question": "What is self attention in transformers?", "top_k": 3})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"] and body["sources"][0]["source"] == "a.pdf"
    assert body["diagnostics"]["chunks_retrieved"] == 3
    s = client.post("/api/search", json={"query": "residual connections ResNet", "top_k": 2})
    assert s.json()["results"][0]["source"] == "b.pdf"


def test_doc_filter_and_compare_and_summarize(client):
    a = upload(client, "a.pdf", PAPER_A).json()["uploaded"][0]["doc_id"]
    b = upload(client, "b.pdf", PAPER_B).json()["uploaded"][0]["doc_id"]
    r = client.post("/api/ask", json={"question": "image classification", "top_k": 4, "doc_ids": [a]})
    assert {c["source"] for c in r.json()["contexts"]} == {"a.pdf"}
    c = client.post("/api/compare", json={"doc_ids": [a, b], "top_k": 2})
    assert c.status_code == 200 and {s["source"] for s in c.json()["sources"]} == {"a.pdf", "b.pdf"}
    s = client.post("/api/summarize", json={"doc_id": a, "style": "key_points"})
    assert s.status_code == 200 and s.json()["diagnostics"]["llm_calls"] >= 1


def test_errors(client):
    assert client.post("/api/ask", json={"question": "anything here"}).status_code == 404
    assert client.post("/api/compare", json={"doc_ids": ["x"]}).status_code == 422
