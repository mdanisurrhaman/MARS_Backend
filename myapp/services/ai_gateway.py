# from myapp.AI.Agents.Qna_Agent.qna_user_agent import qna_agent
# from myapp.AI.Agents.data_analysis.data_analysis.data_analysis_main import run_data_analysis
# from myapp.AI.Agents.talent_sourcing1.talent_main import run_recruitment_crew
# from myapp.AI.Agents.stock_agent.src.new_decision_support.stock_main import run_stock
# from myapp.AI.Agents.resume_optimizer.resume_optimizer.resume_opt_agent import run_resume_opt
# from myapp.AI.Agents.sentiment_analysis.sentiment_tool import run_sentiment
# from myapp.AI.Agents.automation_agent2.src.automation.main import auto_run
# from myapp.AI.Agents.rag_researcher.rag_researcher.src.research import rag_main
# from myapp.AI import main  # Root agent
# from datetime import datetime
# from myapp.AI.Agents.resume_optimizer.resume_optimizer.resume_opt_agent import (
#     ResumeOpt,
#     run_resume_opt,
#     extract_text
# )
# import os

# def call_ai_agent(agent_type, query, file_path=None, csv_file=None):
#     if agent_type == "qna":   #✅
#         return qna_agent(query)

#     elif agent_type == "data":
#         return run_data_analysis(query, file_path)

#     elif agent_type == "talent": #✅raw output setup pending by ai team
#         return run_recruitment_crew(query)

#     elif agent_type == "stock": #✅
#         return run_stock(query)

#     elif agent_type == "resume": #✅
#         try:
#             # Extract resume and JD text (JD can be a string or a file path)
#             resume_text = extract_text(file_path)[:3000]
#             jd_text = extract_text(query)[:3000] if os.path.isfile(query) else query[:3000]

#             # Option 1: Use the shortcut function
#             result = run_resume_opt(file_path, query)

#             # Option 2: Use manual crew (you can switch if needed)
#             result = ResumeOpt().crew().kickoff(inputs={
#                 'resume': resume_text,
#                 'job_description': jd_text
#             })

#             return result

#         except Exception as e:
#             return f"Error in Resume Agent: {str(e)}"

#     elif agent_type == "sentiment": #✅
#         return run_sentiment.func(file_path=file_path, csv_file=csv_file)

#     elif agent_type == "auto": #✅
#         return auto_run(query=query, file_path=file_path, csv_file=csv_file)

#     elif agent_type == "rag": #✅
#         return rag_main.rag_run(query, file_path)

#     elif agent_type == "root":
#         return main.manager_agent_function(query, file_path)

#     else:
#         return {"error": "Invalid agent_type"}


from datetime import datetime
import os

def call_ai_agent(agent_type, query, file_path=None, csv_file=None):
    # QnA Agent
    if agent_type == "qna":
        from myapp.AI.Agents.Qna_Agent.qna_user_agent import qna_agent
        return qna_agent(query)

    # Data Analysis Agent
    elif agent_type == "data":
        from myapp.AI.Agents.data_analysis.data_analysis.data_analysis_main import run_data_analysis
        return run_data_analysis(query, file_path)

    # Talent Sourcing Agent
    elif agent_type == "talent":
        from myapp.AI.Agents.talent_sourcing1.talent_main import run_recruitment_crew
        return run_recruitment_crew(query)

    # Stock Analysis Agent
    elif agent_type == "stock":
        from myapp.AI.Agents.stock_agent.src.new_decision_support.stock_main import run_stock
        return run_stock(query)

    # Resume Optimizer Agent
    elif agent_type == "resume":
        try:
            from myapp.AI.Agents.resume_optimizer.resume_optimizer.resume_opt_agent import (
                ResumeOpt,
                run_resume_opt,
                extract_text,
            )

            resume_text = extract_text(file_path)[:3000]
            jd_text = extract_text(query)[:3000] if os.path.isfile(query) else query[:3000]

            # Shortcut run
            result = run_resume_opt(file_path, query)

            # Manual crew run
            result = ResumeOpt().crew().kickoff(inputs={
                "resume": resume_text,
                "job_description": jd_text,
            })

            return result
        except Exception as e:
            return f"Error in Resume Agent: {str(e)}"

    # Sentiment Analysis Agent
    elif agent_type == "sentiment":
        from myapp.AI.Agents.sentiment_analysis.sentiment_tool import run_sentiment
        return run_sentiment.func(file_path=file_path, csv_file=csv_file)

    # Automation Agent
    elif agent_type == "auto":
        from myapp.AI.Agents.automation_agent2.src.automation.main import auto_run
        return auto_run(query=query, file_path=file_path, csv_file=csv_file)

    # RAG Researcher Agent
    elif agent_type == "rag":
        from myapp.AI.Agents.rag_researcher.rag_researcher.src.research import rag_main
        return rag_main.rag_run(query, file_path)

    # Root AI Agent
    elif agent_type == "root":
        from myapp.AI import main
        return main.manager_agent_function(query, file_path)

    else:
        return {"error": "Invalid agent_type"}
