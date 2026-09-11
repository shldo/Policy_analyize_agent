// Real browser acceptance against the isolated local instance, no mocked API.
const { chromium } = require(process.env.PLAYWRIGHT_PACKAGE);
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const output = path.resolve(process.env.UI_ACCEPTANCE_OUTPUT || 'backend/data/evaluation/ui_acceptance_20260910');
const requestedStage=process.argv[2]||'inspect';
if(['register','direct','agent','full-corpus','followup','network-error'].includes(requestedStage)
  && process.env.UI_ACCEPTANCE_ISOLATED_DB_CONFIRMED!=='1') {
  throw Error('Set UI_ACCEPTANCE_ISOLATED_DB_CONFIRMED=1 only after verifying localhost:8000 uses the disposable database.');
}
fs.mkdirSync(output, {recursive:true});
(async () => {
  const browser = await chromium.launch({channel:'msedge', headless:true});
  const state = path.join(output,'private-browser-state.json');
  const context = await browser.newContext({viewport:{width:1440,height:1000},
    ...(fs.existsSync(state)?{storageState:state}:{})});
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  const errors=[];
  page.on('pageerror', e=>errors.push(e.message));
  const stage=process.argv[2]||'inspect';
  await page.goto('http://127.0.0.1:5300', {waitUntil:'networkidle'});
  if(stage==='register') {
    const credentials={username:'acceptance_'+Date.now(),password:crypto.randomBytes(20).toString('hex')};
    const res=await context.request.post('http://127.0.0.1:8000/api/v1/auth/register',{data:credentials});
    if(!res.ok()) throw Error('Test account creation failed: '+res.status());
    fs.writeFileSync(path.join(output,'private-test-user.json'),JSON.stringify(credentials));
    await page.goto('http://127.0.0.1:5300/login',{waitUntil:'networkidle'});
  }
  if(stage==='login') {
    const credentials=JSON.parse(fs.readFileSync(path.join(output,'private-test-user.json')));
    await page.goto('http://127.0.0.1:5300/login',{waitUntil:'networkidle'});
    await page.locator('form input:not([type="password"])').fill(credentials.username);
    await page.locator('form input[type="password"]').fill(credentials.password);
    await page.getByRole('button',{name:'Log in',exact:true}).click();
    await page.waitForURL('**/chat', {timeout:15000});
    await page.waitForLoadState('networkidle');
  }
  if(stage==='modes') {
    await page.getByText('Agent (ReAct)',{exact:true}).click();
  }
  if(stage==='followup') {
    await page.getByText('What does the provided policy material say about responsible AI staff training?',{exact:true}).first().click();
    const finished=page.waitForResponse(r=>r.url().includes('/chat/stream') && r.request().method()==='POST',{timeout:180000});
    await page.locator('textarea').first().fill('In your previous answer, what event starts the 12-month training deadline? Reply briefly with a citation.');
    await page.getByRole('button',{name:'Send',exact:true}).click();
    const response=await finished;
    await response.finished();
    console.log('followup HTTP status',response.status());
    await page.getByRole('button',{name:'Send',exact:true}).waitFor({timeout:180000});
  }
  if(stage==='reopen' || stage==='pdf') {
    await page.getByText('What does the provided policy material say about responsible AI staff training?',{exact:true}).first().click();
    await page.getByText('Evidence coverage not confirmed',{exact:true}).waitFor();
    if((await page.locator('body').innerText()).includes('The answer has been withheld')) throw Error('Stale refusal banner');
    await page.getByText('6 sources',{exact:false}).first().click();
    await page.getByText('Complete evidence coverage is not confirmed.',{exact:true}).waitFor();
    if(stage==='pdf') {
      await page.evaluate(() => {
        const original = window.open;
        window.open = function(url, ...args) {
          window.__pdfOpenedUrl = url;
          return original.call(window, url, ...args);
        };
      });
      const button = page.getByRole('button', {name:/Open PDF at page/}).first();
      const label = await button.innerText();
      const expected = Number(label.match(/page (\d+)/)[1]);
      const response = page.waitForResponse(r => /\/documents\/[^/]+\/file/.test(r.url()));
      await button.click();
      const pdfResponse = await response;
      if(!pdfResponse.ok()) throw Error('PDF endpoint failed: '+pdfResponse.status());
      const bytes = await pdfResponse.body();
      if(bytes.subarray(0,5).toString() !== '%PDF-') throw Error('Source is not a PDF');
      await page.waitForFunction(() => !!window.__pdfOpenedUrl);
      const opened = await page.evaluate(() => window.__pdfOpenedUrl);
      if(!opened.endsWith('#page='+expected)) throw Error('Wrong PDF page fragment');
      fs.writeFileSync(path.join(output,'pdf-source.pdf'),bytes);
      fs.writeFileSync(path.join(output,'pdf-navigation.json'),JSON.stringify({expected_page:expected,status:pdfResponse.status(),page_fragment_correct:true,sha256:crypto.createHash('sha256').update(bytes).digest('hex')}));
    }
  }
  if(stage==='sources') {
    await page.getByRole('button',{name:'Find files',exact:true}).click();
    await page.waitForLoadState('networkidle');
    await page.getByRole('button',{name:'Add to chat',exact:true}).first().waitFor({timeout:30000});
  }
  if(stage==='agent' || stage==='full-corpus' || stage==='network-error') {
    await page.getByRole('button',{name:'New Chat',exact:true}).click();
    while(await page.getByTitle('Remove from context',{exact:true}).count()) {
      await page.getByTitle('Remove from context',{exact:true}).first().click();
    }
    await page.screenshot({path:path.join(output,stage+'-no-source.png'),fullPage:true});
    await page.getByRole('button',{name:'Find files',exact:true}).click();
    await page.getByRole('button',{name:'Add to chat',exact:true}).last().click();
    await page.getByRole('button',{name:'Go to chat',exact:true}).click();
    if(await page.getByText('Direct',{exact:true}).count()) {
      await page.getByText('Direct',{exact:true}).click();
      await page.getByText('Agent (ReAct)',{exact:true}).click();
    }
    if(stage==='full-corpus') {
      await page.getByText('Document Analysis',{exact:true}).click();
      await page.getByText('Open Discussion',{exact:true}).click();
    }
    if(stage==='network-error') await page.route('**/api/v1/chat/stream', route=>route.abort('connectionfailed'));
    const finished=stage!=='network-error' ? page.waitForResponse(r=>r.url().includes('/chat/stream') && r.request().method()==='POST',{timeout:180000}) : null;
    await page.locator('textarea').first().fill('Compare staff training obligations in the selected Australian policy with human oversight guidance in the Singapore Agentic AI framework. Search the full document library for the Singapore material and cite both sources.');
    await page.getByRole('button',{name:'Send',exact:true}).click();
    if(finished) {
      const response=await finished;
      await response.finished();
      fs.writeFileSync(path.join(output,stage+'-sse.txt'),await response.text());
      console.log('agent HTTP status',response.status());
    } else {
      await page.getByRole('alert').first().waitFor();
    }
    await page.getByRole('button',{name:'Send',exact:true}).waitFor({timeout:180000});
  }
  if(stage==='direct') {
    await page.getByRole('button',{name:'Find files',exact:true}).click();
    await page.getByRole('button',{name:'Add to chat',exact:true}).last().click();
    await page.getByRole('button',{name:'Go to chat',exact:true}).click();
    await page.getByText('Agent (ReAct)',{exact:true}).click();
    await page.getByText('Direct',{exact:true}).click();
    console.log('inputs',await page.locator('textarea').count());
    await page.locator('textarea').first().fill('What does the provided policy material say about responsible AI staff training? Cite the source and state any evidence gaps.');
    const responsePromise=page.waitForResponse(r=>r.request().method()==='POST' && r.url().includes('/chat'),{timeout:180000});
    await page.getByRole('button',{name:'Send',exact:true}).click();
    const response=await responsePromise;
    await response.finished();
    console.log('chat HTTP status',response.status());
    await page.getByRole('button',{name:'Send',exact:true}).waitFor({timeout:120000});
    await page.waitForFunction(()=>!document.body.innerText.includes('Generating'),{timeout:120000});
  }
  await page.screenshot({path:path.join(output,stage+'.png'),fullPage:true});
  const text=await page.locator('body').innerText();
  fs.writeFileSync(path.join(output,stage+'.json'),JSON.stringify({url:page.url(),text,errors},null,2));
  console.log(text);
  await context.storageState({path:state});
  await browser.close();
})().catch(e=>{console.error(e.message);process.exit(1)});
