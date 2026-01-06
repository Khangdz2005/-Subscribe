from __future__ import annotations

import base64
import json
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(title="RSA Encrypt Sandbox", version="1.0.0")


class EncryptRequest(BaseModel):
    # This is the same kind of input you provided:
    # base64 of an inner PEM block (nested).
    public_key_b64: str = Field(..., min_length=1)

    # "JSON thuần" to be encrypted. We will JSON-serialize it
    # similarly to JavaScript JSON.stringify (no spaces).
    payload: Any


class EncryptResponse(BaseModel):
    ciphertext_b64: str


def _decode_nested_pem_from_b64(public_key_b64: str) -> bytes:
    """
    Accepts a base64 string that decodes to an ASCII PEM block.
    (Your sample is base64 of a PEM that itself contains the actual key.)
    """
    # Allow accidental whitespace/newlines.
    public_key_b64 = "".join(public_key_b64.split())
    try:
        raw = base64.b64decode(public_key_b64, validate=True)
    except Exception as e:  # noqa: BLE001
        raise ValueError("public_key_b64 is not valid base64") from e

    # raw should be PEM text (bytes)
    if b"-----BEGIN" not in raw:
        raise ValueError("Decoded public key does not look like PEM text")
    return raw


def _extract_inner_pem_if_needed(pem_text: bytes) -> bytes:
    """
    If pem_text is a PEM wrapper whose body is base64 of another PEM,
    unwrap it once. Otherwise return pem_text as-is.
    """
    lines = [ln.strip() for ln in pem_text.splitlines() if ln.strip()]
    if len(lines) < 3:
        return pem_text

    if lines[0].startswith(b"-----BEGIN") and lines[-1].startswith(b"-----END"):
        body = b"".join(lines[1:-1])
        # If body decodes to another PEM, unwrap it.
        try:
            inner = base64.b64decode(body, validate=True)
        except Exception:
            return pem_text
        if b"-----BEGIN PUBLIC KEY-----" in inner:
            return inner
    return pem_text


def _load_public_key(pem_text: bytes):
    try:
        return serialization.load_pem_public_key(pem_text)
    except Exception as e:  # noqa: BLE001
        raise ValueError("Failed to parse public key PEM") from e


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/encrypt", response_model=EncryptResponse)
def encrypt(req: EncryptRequest):
    # JSON.stringify-like encoding: compact, UTF-8
    try:
        plaintext = json.dumps(req.payload, ensure_ascii=False, separators=(",", ":"))
    except TypeError as e:
        raise HTTPException(status_code=400, detail="payload is not JSON-serializable") from e

    try:
        outer_pem = _decode_nested_pem_from_b64(req.public_key_b64)
        pem = _extract_inner_pem_if_needed(outer_pem)
        pub = _load_public_key(pem)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # RSAES-PKCS1-v1_5 padding (matches JSEncrypt default; NOT OAEP)
    try:
        ciphertext = pub.encrypt(plaintext.encode("utf-8"), padding.PKCS1v15())
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Encryption failed (message too long or bad key)") from e

    return EncryptResponse(ciphertext_b64=base64.b64encode(ciphertext).decode("ascii"))

