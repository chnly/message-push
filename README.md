### run 
在 main.py中
```python
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
执行 python main.py
### poerty 生成requirements.txt
`poetry export -f requirements.txt --output requirements.txt  --without-hashes`

### run in docker
```docker
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7
COPY ./message_push /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
```
