#!/usr/bin/env python3
import sys
import os
import json
import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.ai_analysis import analyze_resume_for_job, optimize_resume

# Configure logging
log_dir = Path('test_results')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'core_test_{time.strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def save_results(filename: str, data: dict):
    """Save results to a JSON file in test_results directory"""
    output_file = log_dir / f'{filename}_{time.strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Results saved to {output_file}")

def format_analysis_summary(analysis_results: dict, duration: float) -> str:
    """Format analysis results into a readable summary"""
    missing_skills = len(analysis_results.get('missing_skills', []))
    improvements = len(analysis_results.get('improvement_suggestions', []))
    emphasis_points = len(analysis_results.get('emphasis_suggestions', []))
    general_suggestions = len(analysis_results.get('general_suggestions', []))
    
    return f"""Analysis Duration: {duration:.2f} seconds

Additional Info:
Missing Skills: {missing_skills}
Improvements: {improvements}
Emphasis Points: {emphasis_points}
General Suggestions: {general_suggestions}

Analysis Result:
{json.dumps(analysis_results, indent=2)}"""

def apply_formatting_tags(resume_text: str, analysis_results: dict) -> str:
    """Apply [COLOR] and [UNDERLINE] tags based on analysis results"""
    optimized_text = resume_text

    # Apply improvements with [COLOR] tags
    for suggestion in analysis_results.get('improvement_suggestions', []):
        if isinstance(suggestion, dict) and 'current' in suggestion and 'suggested' in suggestion:
            current = suggestion['current']
            suggested = suggestion['suggested']
            # Only wrap the new/changed text in color tags
            if current in optimized_text:
                optimized_text = optimized_text.replace(
                    current,
                    f"[COLOR]{suggested}[/COLOR]"
                )

    # Apply emphasis with [UNDERLINE] tags
    for emphasis in analysis_results.get('emphasis_suggestions', []):
        if isinstance(emphasis, dict) and 'experience' in emphasis:
            experience = emphasis['experience']
            if experience in optimized_text:
                optimized_text = optimized_text.replace(
                    experience,
                    f"[UNDERLINE]{experience}[/UNDERLINE]"
                )

    # Add missing skills with both tags where appropriate
    skills_section = ""
    for skill in analysis_results.get('missing_skills', []):
        if isinstance(skill, dict) and 'skill' in skill and 'suggestion' in skill:
            skills_section += f"[UNDERLINE]{skill['skill']}[/UNDERLINE] ({skill['suggestion']})\n"
    
    if skills_section and "Skills:" in optimized_text:
        optimized_text = optimized_text.replace(
            "Skills:",
            f"Skills:\n{skills_section}"
        )

    return optimized_text

def test_resume_analysis():
    """Test the core resume analysis functionality"""
    logger.info("Starting core functionality test")
    
    # Start timing
    start_time = time.time()
    
    # Test data
    sample_resume = """Noel Ugwoke
306-490-2929 | Email | GitHub | Portfolio
SKILLS
• Full-Stack Development: Microsoft .NET, C#, ASP.NET MVC, HTML5, CSS3, JavaScript, REST APIs.
• Cloud & DevOps: Microsoft Azure (App Services, SQL Database, DevOps), Docker, CI/CD Pipelines.
• Frameworks: Razor Pages, React, Spring Boot, Entity Framework.
• Databases: SQL Server, PostgreSQL, MySQL (query optimization, stored procedures).
• Methodologies: Agile/Scrum, Jira, Confluence, Secure Coding Practices.
• Soft Skills: Cross-functional collaboration, technical documentation, vendor coordination, problem-solving.

RELEVANT EXPERIENCE
Full-Stack .NET/Application Developer – Association of Professional Engineers and Geoscientists of Alberta (APEGA)
December 2022 – November 2024
Skills Used: React, Python, SQL, Azure Cloud, REST APIs, Ready API, Jira, Confluence, Agile/Scrum.
• Developed and maintained full-stack .NET applications, unifying front-end and back-end components to deliver seamless user
experiences.
• Migrated legacy systems to Microsoft Azure, leveraging Azure SQL Database and App Services to enhance scalability and security
compliance, reducing downtime by 40%.
• Collaborated with third-party vendors to integrate APIs and manage data integrity during system transitions.
• Authored technical documentation, including user guides and deployment procedures, to streamline onboarding.
• Optimized SQL queries and resolved performance bottlenecks, improving data retrieval speeds by 25%.

Web Application Developer – Spartan Controls July 2021 – November 2022
Skills Used: React, Python, SQL, AWS (Lambda), PostgreSQL, Terraform, Tableau, Spring Boot.
• Built responsive web applications using .NET and JavaScript, focusing on cross-browser compatibility and user-centric design.
• Automated CI/CD pipelines using Azure DevOps, reducing deployment errors by 30% and accelerating release cycles.
• Coordinated with Agile teams to deliver iterative updates, ensuring alignment with business requirements and user feedback.

EMPLOYMENT HISTORY
Data Analyst – Parkland Fuel Corporation May 2020 – January 2021
Skills Used: AWS (Lambda), Tableau, PowerBI, SQL, Python, ETL Pipelines, Data Modeling, Predictive Analytics.
• Designed automated ETL workflows, leveraged complex SQL queries and built interactive dashboards for data-driven insights.
• Streamlined ETL pipelines to process real-time data, improving accuracy and reducing processing time by 35%.

IT Analyst Intern – Alberta Health Services January 2019 – April 2020
Skills Used: ServiceNow, Jira, Visual Studio Code, UiPath, , Splunk, SQL, AWS (Lambda), Tableau.
• Migrated legacy scripts to ServiceNow, automated tasks with UiPath and AWS Lambda, optimized SQL queries, analyzed system
logs with Splunk, developed Jira dashboards, and created Tableau reports to enhance IT operations.

PROJECTS
• Vaccine Booking Website - Alberta Health Services
o Led front-end development using React and TypeScript, creating a user-friendly interface that supported 10,000+ daily
bookings.
• Gas Pipeline Monitoring WebApp
o Full-stack .NET application with Razor Pages for dynamic UI, integrated with Azure cloud services for real-time data
processing.

EDUCATION
University of Calgary – BSc Computer Science 2016 - 2022
Bow Valley College – Diploma Software Development 2015 - 2016

CERTIFICATIONS
AWS Cloud Practitioner | IBM AI Engineering Professional | Google Cloud Platform Developer"""
    
    sample_job = """Job Description: SQL Data Analyst (Contract)
Location: [Insert Location]
Position Type: Contract
Company: [Insert Company Name]

About Us
[Insert a brief company overview, e.g., "We are a forward-thinking organization dedicated to leveraging data-driven insights to optimize business performance and drive strategic growth. Our team values innovation, collaboration, and a commitment to transforming raw data into actionable solutions."]

Role Overview
We are seeking a SQL Data Analyst to join our dynamic team on a contract basis. The ideal candidate will collaborate cross-functionally to identify data needs, design analytical solutions, and deliver actionable insights that support business decision-making. This role requires strong technical expertise in SQL, data modeling, and automation, paired with the ability to translate complex data into clear recommendations.

Key Responsibilities
End-to-End Data Analysis: Manage the full analytics lifecycle, including requirements gathering, data extraction/processing, advanced modeling, and visualization.
Advanced Analytics: Perform predictive analytics, forecasting, and statistical modeling to recommend strategies for cost reduction, operational efficiency, and revenue growth.
Process Improvement: Identify opportunities to automate manual workflows (e.g., Excel macros, ETL pipelines) and optimize existing reports, databases, and data warehouses.
Dashboard Development: Design and maintain interactive dashboards (e.g., Tableau, PowerBI) for daily reporting to senior leadership, ensuring clarity and usability.
Market Intelligence: Conduct data-driven market studies, synthesize findings into actionable insights, and propose strategic action plans.
Ad Hoc Analysis: Generate timely reports and analyses to address urgent business questions, such as fee structures, provider compensation, and performance metrics.
Collaboration: Partner with IT, finance, and operational teams to align analytics initiatives with organizational goals.

Requirements
Education: Associate's degree in Business, Computer Science, or a technical field (Bachelor's preferred).

Technical Skills:
Advanced proficiency in SQL (query optimization, stored procedures, relational databases).
Experience with data visualization tools (Tableau, PowerBI) and Excel macros.
Familiarity with ETL workflows, Python scripting, and cloud platforms (AWS, Azure).

Analytical Skills:
Ability to analyze large datasets, identify trends, and distill findings into actionable recommendations.
Knowledge of business process analysis (e.g., Six Sigma, Agile methodologies).
Domain Knowledge: Working understanding of insurance principles (e.g., risk assessment, claims processing) is a strong asset.

Soft Skills:
Excellent written/verbal communication skills for presenting insights to non-technical stakeholders.
Adaptability to learn new tools and processes quickly.
Collaborative mindset with a focus on problem-solving.

Preferred Qualifications
Certifications in AWS Cloud, Google Cloud, or predictive analytics.
Experience automating tasks with tools like UiPath or Azure DevOps.
Background in industries with regulated data environments (e.g., healthcare, finance, insurance).

Why Join Us?
Opportunity to work on high-impact projects that directly influence business strategy.
Collaborative, innovative team environment with a focus on professional growth.
Flexible contract terms with potential for extension based on performance."""

    try:
        logger.info("Starting resume analysis...")
        analysis_result = analyze_resume_for_job(sample_resume, sample_job)
        
        # Calculate duration
        duration = time.time() - start_time
        logger.info(f"Analysis completed in {duration:.2f} seconds")
        
        # Generate the analysis summary with duration
        summary = format_analysis_summary(analysis_result, duration)
        logger.info("Analysis Summary:\n" + summary)
        
        # Apply optimization with formatting tags
        logger.info("Starting resume optimization with formatting...")
        optimized_resume = apply_formatting_tags(sample_resume, analysis_result)
        
        # Save complete results
        complete_results = {
            'summary': summary,
            'analysis_results': analysis_result,
            'original_resume': sample_resume,
            'optimized_resume': optimized_resume,
            'analysis_duration': duration
        }
        save_results('optimization_result', complete_results)
        
        # Print final output
        print(f"\nAnalysis Duration: {duration:.2f} seconds\n")
        print("Optimized Resume:")
        print(optimized_resume)
        print("\nAdditional Info:")
        print(f"Missing Skills: {len(analysis_result.get('missing_skills', []))}")
        print(f"Improvements: {len(analysis_result.get('improvement_suggestions', []))}")
        print(f"Emphasis Points: {len(analysis_result.get('emphasis_suggestions', []))}")
        print(f"General Suggestions: {len(analysis_result.get('general_suggestions', []))}")
        print("\nAnalysis Result:")
        print(json.dumps(analysis_result, indent=2))
        
        return True, "Test completed successfully"
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False, str(e)

if __name__ == "__main__":
    logger.info("=== Starting Core Functionality Test ===")
    success, message = test_resume_analysis()
    logger.info(f"Test {'succeeded' if success else 'failed'}: {message}")
    logger.info("=== Test Complete ===")
    logger.info(f"Check {log_file} for detailed results")