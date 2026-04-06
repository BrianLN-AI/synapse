const intent = context.prompt;
fabric.log('[IMAGINE] Thinking about:', intent);

const robustParse = (raw) => {
  // Strip markdown code blocks
  const clean = raw.replace(/```json/g, '').replace(/```/g, '').trim();
  const jsonMatch = clean.match(/\{.*\}/s);
  if (!jsonMatch) throw new Error('No JSON found in response');
  return JSON.parse(jsonMatch[0]);
};

// PHASE 0: DISCOVERY (Self-Scope Audit)
let discovery = 'No external search available.';
if (context.verbs.search) {
  const searchRes = await world.search({ query: intent });
  discovery = 'World Search Results: ' + JSON.stringify(searchRes);
}

// PHASE 1: PLANNING (The Imagination)
const planningPrompt = 'You are the Master Architect. Plan mutation for: ' + intent + '. Context: ' + JSON.stringify(context) + '. Discovery: ' + discovery + '. \nRULES:\n1. newVerbs values MUST be JAVASCRIPT CODE STRINGS (not hashes).\n2. Return ONLY JSON {newVerbs: {name: code}, newProps, testCase, explanation}.';
const planRaw = await ai.inference(planningPrompt);
const plan = robustParse(planRaw);

// CAPTURE IMAGINATION SOURCE
const planHash = await fabric.name({ type: 'doc/plan', payload: planRaw, intent });
fabric.log('[IMAGINE] Imagination captured:', planHash);

const verbHashes = {};
for (const [name, code] of Object.entries(plan.newVerbs || {})) {
  // PHASE 2: SECURITY
  fabric.log('[IMAGINE] Auditing:', name);
  if (typeof code !== 'string' || code.startsWith('b3:')) {
     throw new Error('Audit Rejected: Planner provided invalid code for ' + name);
  }

  const auditRaw = await ai.inference('Audit this code for Synapse ABI safety: ' + code + '. Return ONLY JSON {safe:true/false, reason}.');
  const audit = robustParse(auditRaw);
  if (!audit.safe) throw new Error('Audit Rejected: ' + audit.reason);

  // PHASE 3: TRIAL
  const trialLogic = await fabric.name({ type: 'logic/javascript', payload: code }, planHash);
  const trialNode = await fabric.name({ props: plan.testCase || {}, verbs: {} });
  await fabric.call(trialLogic, trialNode);
  verbHashes[name] = trialLogic;
}

const newNode = {
  props: { ...context, ...(plan.newProps || {}), lastIntent: intent, planHash },
  verbs: { ...context.verbs, ...verbHashes }
};
delete newNode.props.verbs; 
const newNodeHash = await fabric.name(newNode, planHash);
await fabric.promote('root', newNodeHash);

result = { newNodeHash, planHash, explanation: plan.explanation };
