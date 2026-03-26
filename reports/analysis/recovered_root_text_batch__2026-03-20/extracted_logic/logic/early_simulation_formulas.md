# text early sim logic

Source: `text_early_sim_logic.txt`

```text
S_{new} = S_{old} + \alpha(E_{success}) - \beta(E_{failure})

Q(s, a) = Q(s, a) + \alpha \big( R + \gamma \max_{a'} Q(s', a') - Q(s, a) \big)

T_{new} = T_{old} - \lambda(B) + \delta(A)

Public_Opinion = Policy_Success - Scandals + Economic_Stability

AI_Faction_Strategy = P(negotiation | past_success) + P(war | military_strength)

Political_Loyalty = Ideological_Alignment - Past_Betrayals + Personal_Relationships

Event_Trigger = P(Scientific_Breakthrough) + P(Economic_Collapse) + P(Civil_War)

P(support) = Ideological_Alignment + Political_Ambition - Risk_Assessment
```
