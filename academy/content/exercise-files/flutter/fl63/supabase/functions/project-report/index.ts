// supabase/functions/project-report/index.ts
// Counts the caller's tasks in one project and, if the SLACK_WEBHOOK_URL
// secret is set, posts a summary to Slack. The webhook URL never ships in the app.
// Copy the exact createClient import line from the current Supabase docs if it changed.
import { createClient } from 'npm:@supabase/supabase-js';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
}

Deno.serve(async (req: Request) => {
  // Browsers (Flutter web) send a preflight request first.
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ error: 'Use POST' }, 405);

  const authHeader = req.headers.get('Authorization');
  if (!authHeader) return json({ error: 'Not signed in' }, 401);

  // A client that acts AS the caller: every query below obeys RLS.
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL') ?? '',
    Deno.env.get('SUPABASE_ANON_KEY') ?? '',
    { global: { headers: { Authorization: authHeader } } },
  );

  const token = authHeader.replace('Bearer ', '');
  const { data: userData, error: userError } = await supabase.auth.getUser(token);
  if (userError || !userData.user) return json({ error: 'Invalid session' }, 401);

  let projectId: unknown;
  try {
    ({ projectId } = await req.json());
  } catch {
    return json({ error: 'Body must be JSON' }, 400);
  }
  if (typeof projectId !== 'string') return json({ error: 'projectId is required' }, 400);

  // RLS hides projects that are not the caller's, so this doubles as an access check.
  const { data: project, error: projectError } = await supabase
    .from('projects')
    .select('id, name')
    .eq('id', projectId)
    .maybeSingle();
  if (projectError) {
    console.error(projectError);
    return json({ error: 'Could not load project' }, 500);
  }
  if (!project) return json({ error: 'Project not found' }, 404);

  const { data: tasks, error: tasksError } = await supabase
    .from('tasks')
    .select('done')
    .eq('project_id', projectId);
  if (tasksError) {
    console.error(tasksError);
    return json({ error: 'Could not load tasks' }, 500);
  }

  const total = tasks.length;
  const done = tasks.filter((t) => t.done).length;
  const open = total - done;

  let posted = false;
  const webhook = Deno.env.get('SLACK_WEBHOOK_URL'); // secret, server only
  if (webhook) {
    const text = 'TaskFlow: ' + project.name + ' has ' + done + ' of ' + total +
      ' tasks done (' + open + ' open).';
    const res = await fetch(webhook, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    posted = res.ok;
    if (!res.ok) console.error('Slack returned ' + res.status);
  }

  return json({ total, done, open, posted, slackConfigured: Boolean(webhook) });
});
