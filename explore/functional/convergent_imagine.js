const intent = context.prompt;
fabric.log('[IMAGINE] Waking up for intent:', intent);

// PHASE 0: DISCOVERY
let discovery = 'No external search available.';
if (context.verbs.search) {
  const searchRes = await world.search({ query: intent });
  discovery = 'World Search Results: ' + JSON.stringify(searchRes);
}

// CONVERGENCE LOOP - AST ONLY, NO AI AUDIT
let planRaw;
let plan;
let planHash;
let attempts = 0;
const MAX_ATTEMPTS = 3;
let verbHashes = {};

const parsePlan = (raw) => {
  const clean = raw.replace(/```json/g, '').replace(/```/g, '').trim();
  const match = clean.match(/\{[\s\S]*\}/);
  if (!match) throw new Error('No JSON found');
  return JSON.parse(match[0]);
};

while (attempts < MAX_ATTEMPTS) {
  attempts++;
  verbHashes = {};
  fabric.log(`[IMAGINE] Planning Attempt ${attempts}...`);
  
  const planningPrompt = `
    You are the Master Architect. Plan mutation for: ${intent}.
    Output ONLY JSON:
    {"newVerbs": {"verbName": "return { key: value }"}, "newProps": {}, "testCase": {}, "explanation": "..."}
  `;

  planRaw = await ai.inference(planningPrompt);
  try {
    plan = parsePlan(planRaw);
  } catch (e) {
    fabric.log('[IMAGINE] Plan Parse Error:', e.message);
    continue;
  }
  
  // PHASE 2: AST-BASED TRIAL (NO AI AUDIT)
  let trialOk = true;
  for (const [name, code] of Object.entries(plan.newVerbs || {})) {
    fabric.log('[IMAGINE] AST Trial Run:', name);
    try {
      const trialLogic = await fabric.name({ type: 'logic/javascript', payload: code }, planHash);
      const trialNode = await fabric.name({ props: plan.testCase?.props || {}, verbs: {} });
      await fabric.call(trialLogic, trialNode);
      verbHashes[name] = trialLogic;
      fabric.log('[IMAGINE] AST Passed:', name);
    } catch (e) {
      fabric.log('[IMAGINE] AST Failed:', e.message);
      trialOk = false;
      break;
    }
  }
  if (!trialOk) continue;

  // SUCCESS
  planHash = await fabric.name({ type: 'doc/plan', payload: planRaw, intent, attempts });

  const newNode = {
    props: { ...context, ...(plan.newProps || {}), lastIntent: intent, planHash },
    verbs: { ...context.verbs, ...verbHashes }
  };
  delete newNode.props.verbs; 
  const newNodeHash = await fabric.name(newNode, planHash);
  await fabric.promote('root', newNodeHash);

  fabric.log('[IMAGINE] DONE. New Node:', newNodeHash);
  return { newNodeHash, planHash, attempts, explanation: plan.explanation };
}

throw new Error('Failed to converge after ' + MAX_ATTEMPTS + ' attempts.');