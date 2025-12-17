import requests, json

def publish_linkedin_post(org_urn, access_token, post_text):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202510"
    }
    payload = {
        "author": org_urn,
        "lifecycleState": "PUBLISHED",
        "commentary": post_text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED"
        }
    }
    api_url = "https://api.linkedin.com/rest/posts"
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  
        post_urn = response.headers.get("x-restli-id")

        if post_urn:
            post_id = post_urn.split(":")[-1]
            post_url = f"https://www.linkedin.com/feed/update/{post_id}/"
            post_object = {
                "post_urn": post_urn,
                "post_id": post_id,
                "post_url": post_url
            }
            print("\033[92mPost published successfully!\033[0m")
            #print("Post published successfully!")
            print(f"Post URL: {post_url}")
            return post_object
        else:
            print("Success response but could not find 'x-restli-id' header.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API call: {e}")
        if 'response' in locals() and response.text:
            print(f"Error details: {response.text}")
        return None

def main():
    ORG_URN = "urn:li:organization:109573414"
    ACCESS_TOKEN = "AQXZ9DGnlPHsZImVe_4T_aqzij_i1Q1IpBtSRifpdO3xknIgHccIIHFg3HowXE4YO5LUFJ1Fw4iaHtR5Fw2mmKrcTkmvThJMVWRxj-CnCtBtKJxapdil7owOU9gLyG1DaRWEwZ5T_kNJWrPW_4yBn9GdW0s1b-yiDQkaPFNJJbbuWwaID0GD1Dl7I6y8v4nXBkWgepjI5POas0_g8yWJjX6oXHu4lIzx5jH22sTxv4AVmnojqQuzE2Rsdyox2g3dse5MZlbiPVB2Esh5k81gecNcu7nFeheUSGVanyjHpfqQThAF9fEBPvGSR8aI61htlv549qf0WLDCWl8xPxjhBx7v6_2Ozg"
    POST_TEXT = ("Hello Everyone! This is a post created for collecting sample resumes for my Dissertation project.\n"
             "Please help me by applying for the position with your resumes.\n"
             "For applying the position please fill the form below:\n"
             "https://docs.google.com/forms/d/e/1FAIpQLSdSACdRA6KOjY-SXQl0unwXJK3_dxDFSrQyECKqpWCZ1EfnPw/viewform?usp=sharing&ouid=111372244744191018484\n"
             "Thank you for your response!\n"
             "#LinkedInAPI #Automation #POC")
    post_info = publish_linkedin_post(ORG_URN, ACCESS_TOKEN, POST_TEXT)
    print(json.dumps(post_info, indent=4))

if __name__ == "__main__":
    main()