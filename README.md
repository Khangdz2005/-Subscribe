# RSA/JSEncrypt sandbox (giả lập môi trường mã hoá)

Repo này có script tối giản để mã hoá một chuỗi/JSON bằng **RSA public key** theo đúng hành vi `JSEncrypt.encrypt()` (output là **base64 ciphertext**).

## Cách dùng

1) Dán public key PEM của bạn vào file `public.pem` (giữ nguyên header/footer):

- `-----BEGIN PUBLIC KEY-----`
- `-----END PUBLIC KEY-----`

2) Mã hoá trực tiếp một chuỗi (ví dụ JSON):

```bash
npm run encrypt -- --pub ./public.pem --data '{"hello":"world"}'
```

3) Hoặc mã hoá từ file:

```bash
echo '{"hello":"world"}' > payload.json
npm run encrypt -- --pub ./public.pem --data-file ./payload.json
```

Kết quả in ra stdout là **ciphertext base64**.

## Ghi chú

- Script này chỉ mô phỏng thao tác **mã hoá RSA bằng public key** (không thực hiện gửi request hay xử lý thanh toán).
- Nếu `Encrypt failed`, thường là do **key PEM sai format** hoặc **plaintext quá dài** so với độ dài key RSA/padding.