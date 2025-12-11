FROM python:3.11-slim

RUN mkdir -p /var/log/django && \
    chmod 755 /var/log/django

# 使用与基础镜像匹配的testing源
RUN set -eux; \
    rm -f /etc/apt/sources.list /etc/apt/sources.list.d/*; \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie main" > /etc/apt/sources.list; \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ trixie-updates main" >> /etc/apt/sources.list; \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security/ trixie-security main" >> /etc/apt/sources.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libjpeg-dev \
        zlib1g-dev \
        libssl-dev \
        libffi-dev \
        curl \
        tzdata \
        netcat-openbsd; \
    rm -rf /var/lib/apt/lists/*; \
    apt-get clean

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# 使用清华pip源
RUN pip install --no-cache-dir -r /app/requirements.txt \
        -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
        --trusted-host pypi.tuna.tsinghua.edu.cn \
        --extra-index-url https://mirrors.aliyun.com/pypi/simple/

COPY . /app
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]