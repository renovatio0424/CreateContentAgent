# MCP Server 연동 설정 가이드

## Claude Code (OpenClaw)에 MCP Server 등록

`~/.claude/claude.json` 파일에 아래 내용을 추가하세요:

```json
{
  "mcpServers": {
    "content-agent": {
      "command": "python",
      "args": ["/Users/reno/Desktop/ToyProject/CreateContentAgent/server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your-anthropic-api-key",
        "OPENAI_API_KEY": "your-openai-api-key",
        "GOOGLE_API_KEY": "your-google-api-key",
        "WORDPRESS_KO_URL": "https://your-ko-blog.com",
        "WORDPRESS_KO_USER": "admin",
        "WORDPRESS_KO_PASSWORD": "your-app-password",
        "WORDPRESS_EN_URL": "https://your-en-blog.com",
        "WORDPRESS_EN_USER": "admin",
        "WORDPRESS_EN_PASSWORD": "your-app-password",
        "COUPANG_AFFILIATE_ID": "your-id",
        "AMAZON_PARTNER_TAG": "your-tag-20",
        "OLLAMA_BASE_URL": "http://localhost:11434"
      }
    }
  }
}
```

## Ollama 모델 준비

```bash
ollama pull llama3.2
ollama pull qwen2.5
```

## 사용 방법

Claude Code에서 다음과 같이 사용하세요:

1. **파이프라인 실행**
   ```
   "에어프라이어 컨텐츠 파이프라인 실행해줘"
   → run_pipeline(category="에어프라이어") 자동 호출
   → 초안 생성 완료 + 큐 ID 수신
   ```

2. **검토 큐 확인**
   ```
   "검토할 컨텐츠 있어?"
   → get_review_queue() 자동 호출
   → 대기 중인 초안 목록 표시
   ```

3. **승인 및 게시**
   ```
   "이 초안 게시해줘 (ID: abc123)"
   → approve_and_publish(draft_id="abc123") 자동 호출
   → WordPress KO + EN 동시 게시
   ```

4. **거절**
   ```
   "이 초안 퀄리티가 안 좋아, 삭제해줘"
   → reject_draft(draft_id="abc123", reason="퀄리티 부족") 자동 호출
   ```

## 주의사항

1. `.env` 파일에 실제 API 키 입력 후 사용
2. WordPress Application Password 생성 필요 (설정 → 사용자 → 프로필)
3. Amazon PA-API는 Associates 계정 승인 후 사용 가능
4. Claude Code 재시작 후 MCP 서버 등록 확인
