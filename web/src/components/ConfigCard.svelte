<script>
  import { createEventDispatcher } from 'svelte'
  import Info from './Info.svelte'

  export let alpha = 1
  export let beta = 1
  export let gamma = 1
  export let delta = 1
  export let resourceBudget = 10
  export let timeSteps = 120
  export let pickDiverseStartNodes = true
  export let startIndex = 0
  export let seed = 0
  export let pEvent = 0.3
  export let numRuns = 200
  export let includeEfficiencySweep = false

  export let status = 'idle'
  export let message = ''

  const dispatch = createEventDispatcher()
  function start() { dispatch('start') }
</script>

<div class="space-y-4 rounded-xl border bg-white p-5 shadow-sm">
  <div>
    <div class="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Game parameters</div>
    <div class="grid grid-cols-2 gap-2">
      <label class="text-sm">
        <div class="flex items-center justify-between"><span>Alpha</span><Info text="Defender reward when the attacked node is covered." /></div>
        <input type="number" step="0.1" class="mt-1 w-full rounded-lg border p-2" bind:value={alpha} />
      </label>
      <label class="text-sm">
        <div class="flex items-center justify-between"><span>Beta</span><Info text="Defender loss when the attacked node is uncovered." /></div>
        <input type="number" step="0.1" class="mt-1 w-full rounded-lg border p-2" bind:value={beta} />
      </label>
      <label class="text-sm">
        <div class="flex items-center justify-between"><span>Gamma</span><Info text="Attacker reward when the attacked node is uncovered." /></div>
        <input type="number" step="0.1" class="mt-1 w-full rounded-lg border p-2" bind:value={gamma} />
      </label>
      <label class="text-sm">
        <div class="flex items-center justify-between"><span>Delta</span><Info text="Attacker loss when the attacked node is covered." /></div>
        <input type="number" step="0.1" class="mt-1 w-full rounded-lg border p-2" bind:value={delta} />
      </label>
    </div>
    <label class="mt-2 block text-sm">
      <div class="flex items-center justify-between"><span>Resource budget</span><Info text="Resource budget K. In this app, it is interpreted as the number of patrol units and also drives the patrol simulation unit count." /></div>
      <input type="number" min="1" step="1" class="mt-1 w-full rounded-lg border p-2" bind:value={resourceBudget} />
    </label>
  </div>

  <div>
    <div class="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Patrol</div>
    <div class="grid grid-cols-2 gap-2">
      <label class="text-sm">
        <div class="flex items-center justify-between"><span>Time steps</span><Info text="Length of the simulated route (t = 0..T)." /></div>
        <input type="number" class="mt-1 w-full rounded-lg border p-2" bind:value={timeSteps} />
      </label>
      <label class="text-sm">
        <div class="flex items-center justify-between"><span>Seed</span><Info text="Random seed for reproducible simulation." /></div>
        <input type="number" class="mt-1 w-full rounded-lg border p-2" bind:value={seed} />
      </label>
    </div>
    <label class="mt-3 flex items-start gap-3 rounded-lg border p-3 text-sm">
      <input
        type="checkbox"
        class="mt-0.5 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
        bind:checked={pickDiverseStartNodes}
      />
      <div>
        <div class="flex items-center gap-2">
          <span>Pick diverse start nodes</span>
          <Info text="When enabled, ALMA chooses far-apart starting nodes automatically. When disabled, all units start from the start index below." />
        </div>
      </div>
    </label>
    <label class="mt-3 block text-sm">
      <div class="flex items-center justify-between"><span>Start index</span><Info text="Index in the node list where all units start (0-based). Disabled when diverse starting nodes are selected." /></div>
      <input
        type="number"
        class="mt-1 w-full rounded-lg border p-2 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500"
        bind:value={startIndex}
        disabled={pickDiverseStartNodes}
      />
    </label>
  </div>

  <div>
    <div class="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Evaluation</div>
    <div class="grid grid-cols-2 gap-2">
      <label class="text-sm">
        <div class="flex items-center justify-between"><span>p(event)</span><Info text="Probability a crime occurs at a timestep in the simulation." /></div>
        <input type="number" step="0.01" min="0" max="1" class="mt-1 w-full rounded-lg border p-2" bind:value={pEvent} />
      </label>
      <label class="text-sm">
        <div class="flex items-center justify-between"><span>Runs</span><Info text="Number of Monte Carlo runs for efficiency evaluation." /></div>
        <input type="number" min="1" class="mt-1 w-full rounded-lg border p-2" bind:value={numRuns} />
      </label>
    </div>
    <label class="mt-3 flex items-start gap-3 rounded-lg border p-3 text-sm">
      <input
        type="checkbox"
        class="mt-0.5 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
        bind:checked={includeEfficiencySweep}
      />
      <div>
        <div class="flex items-center gap-2">
          <span>Efficiency comparison graph</span>
          <Info text="Optionally compute the by-units comparison sweep after the main plan finishes. This is slower and loads separately." />
        </div>
        <div class="mt-1 text-xs text-slate-500">
          Main results load first. The chart is fetched in a second step.
        </div>
      </div>
    </label>
  </div>

  <button
    class="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-3 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-70"
    on:click={start}
    disabled={status === 'running'}
  >
    {#if status === 'running'}
      <span class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></span>
      <span>Building plan</span>
    {:else}
      <span>Start</span>
    {/if}
  </button>
  {#if status !== 'idle'}
    <div class="flex items-center gap-2 text-sm text-gray-600">
      {#if status === 'running'}
        <span class="h-3 w-3 animate-spin rounded-full border-2 border-slate-400 border-t-transparent"></span>
      {/if}
      <span>{status === 'running' ? 'Running' : status}: {message}</span>
    </div>
  {/if}
</div>
