# ---------------- AGENT LAYER (NON-INTRUSIVE) ----------------

class HRChatAgent:
    def __init__(self):
        self.tools = {
            "JOB_POST": self.job_post_agent,
            "SCAN_RESUME": self.scan_resume_agent,
            "SHOW_OPEN_POSITIONS": self.show_open_positions_agent,
            "MATCH_PROFILES": self.rank_profiles,
            "UPDATE_JOB_STATUS": self.update_job_status_agent,
            "END_CHAT": self.end_chat_agent
        }

    def run(self, intent: str):
        handler = self.tools.get(intent, self.unknown_agent)
        return handler()

    def job_post_agent(self):
        return {
            "action": "JOB_POST",
            "message": "📝 Agent activated job posting capability."
        }

    def scan_resume_agent(self):
        return {
            "action": "SCAN_RESUME",
            "message": "📄 Agent activated resume scanning capability."
        }

    def show_open_positions_agent(self):
        return {
            "action": "SHOW_OPEN_POSITIONS",
            "message": "📋 Here are the open positions:"
        }

    def end_chat_agent(self):
        return {
            "action": "END_CHAT",
            "message": "👋 Agent decided to end the chat."
        }
    
    def update_job_status_agent(self):
        return {
            "action": "UPDATE_JOB_STATUS",
            "message": "🔄 Agent activated job status update capability."
        }

    def rank_profiles(self):
        return {
            "action": "MATCH_PROFILES",
            "message": "📋 Here are the matched profiles:"
        }
    
    def unknown_agent(self):
        return {
            "action": "UNKNOWN",
            "message": "❓ Agent could not determine a valid action."
        }
