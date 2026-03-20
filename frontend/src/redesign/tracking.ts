import { postUiEvent } from "../lib/api";

export function trackUiEvent(
  eventName: string,
  payload: {
    route?: string;
    planNumber?: string;
    status?: string;
    context?: Record<string, unknown>;
  } = {},
) {
  void postUiEvent({
    event_name: eventName,
    route: payload.route,
    plan_number: payload.planNumber,
    status: payload.status,
    context: payload.context,
  }).catch(() => {
    // UI instrumentation must never block product workflows.
  });
}
