/** Actionable model failures, kept separately from program discovery and the person's connection choices. */
export function agentConnectionIssue(error) {
  const message = String(error?.message ?? error ?? '').trim();
  if (!message) return null;
  // A temporary rate limit (429) is not evidence that a plan or balance is exhausted.
  const quota = /free usage limit reached|quota (?:exceeded|exhausted)|insufficient[_ ](?:quota|balance|credits)|(?:usage|spending|credit) limit (?:reached|exceeded)|(?:额度|余额)(?:已)?(?:用尽|耗尽|不足)/i;
  const credentials = /no API key for provider route|missing[_ ]api[_ ]key|API key (?:is )?(?:missing|not (?:set|configured)|required)|(?:no|missing) credentials for (?:provider|model)|(?:模型|提供商).*(?:缺少|未配置).*(?:凭据|密钥)/i;
  const kind = quota.test(message) ? 'quota' : credentials.test(message) ? 'credentials' : null;
  return kind ? { kind, message: message.slice(0, 2000) } : null;
}
