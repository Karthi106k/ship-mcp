#!/usr/bin/env python3
"""
Utility to convert Postman collection to MCP tools and OHIP client methods.
Run this script after exporting your Postman collection as JSON.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def parse_postman_collection(collection_path: str) -> Dict[str, Any]:
    """Parse Postman collection JSON file."""
    with open(collection_path, 'r') as f:
        return json.load(f)


def generate_mcp_tool(request: Dict[str, Any]) -> Dict[str, Any]:
    """Generate MCP tool definition from Postman request."""
    name = request.get('name', 'unknown_endpoint').lower().replace(' ', '_')
    description = request.get('description', f"Execute {request.get('name', 'unknown')} operation")
    
    # Extract parameters from URL and body
    properties = {}
    required = []
    
    # Parse URL parameters
    url = request.get('url', {})
    if isinstance(url, str):
        # Simple URL string
        pass
    elif isinstance(url, dict):
        # URL object with query parameters
        query = url.get('query', [])
        for param in query:
            param_name = param.get('key', '')
            param_desc = param.get('description', f'Query parameter {param_name}')
            properties[param_name] = {
                "type": "string",
                "description": param_desc
            }
            if not param.get('disabled', False):
                required.append(param_name)
    
    # Parse body parameters
    body = request.get('body', {})
    if body.get('mode') == 'raw':
        try:
            raw_body = json.loads(body.get('raw', '{}'))
            for key, value in raw_body.items():
                properties[key] = {
                    "type": "string" if isinstance(value, str) else "number" if isinstance(value, (int, float)) else "object",
                    "description": f"Body parameter {key}"
                }
                required.append(key)
        except json.JSONDecodeError:
            pass
    elif body.get('mode') == 'formdata':
        for param in body.get('formdata', []):
            param_name = param.get('key', '')
            param_desc = param.get('description', f'Form parameter {param_name}')
            properties[param_name] = {
                "type": "string",
                "description": param_desc
            }
            if not param.get('disabled', False):
                required.append(param_name)
    
    return {
        "name": f"ohip_{name}",
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }


def generate_client_method(request: Dict[str, Any]) -> str:
    """Generate Python method for OHIP client."""
    name = request.get('name', 'unknown_endpoint').lower().replace(' ', '_')
    method = request.get('method', 'GET').upper()
    
    # Extract URL
    url = request.get('url', {})
    if isinstance(url, str):
        endpoint = url
    elif isinstance(url, dict):
        raw_url = url.get('raw', '')
        # Extract path from URL
        if '{{baseUrl}}' in raw_url:
            endpoint = raw_url.replace('{{baseUrl}}', '').split('?')[0]
        else:
            # Try to extract path
            import re
            match = re.search(r'https?://[^/]+(/.*?)(?:\?|$)', raw_url)
            endpoint = match.group(1) if match else '/unknown'
    else:
        endpoint = '/unknown'
    
    method_code = f'''
    async def {name}(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute {request.get('name', 'unknown')} operation."""
        logger.info(f"Executing {name} with params: {{params}}")
        
        # Extract parameters and prepare request
        query_params = {{}}
        body_data = {{}}
        
        # TODO: Map params to query_params and body_data based on your API
        
        try:
            result = await self._make_request("{method}", "{endpoint}", data=body_data, params=query_params)
            
            return {{
                "status": "success",
                "message": "{request.get('name', 'Operation')} completed successfully",
                "data": result
            }}
        except Exception as e:
            logger.error(f"Error in {name}: {{e}}")
            raise Exception(f"Failed to execute {name}: {{str(e)}}")
'''
    
    return method_code


def main():
    """Main function to convert Postman collection."""
    if len(sys.argv) != 2:
        print("Usage: python postman_converter.py <postman_collection.json>")
        sys.exit(1)
    
    collection_path = sys.argv[1]
    if not Path(collection_path).exists():
        print(f"Error: File {collection_path} not found")
        sys.exit(1)
    
    print(f"Converting Postman collection: {collection_path}")
    
    try:
        collection = parse_postman_collection(collection_path)
        
        # Extract requests from collection
        requests = []
        
        def extract_requests(items):
            for item in items:
                if 'request' in item:
                    requests.append(item)
                elif 'item' in item:
                    extract_requests(item['item'])
        
        extract_requests(collection.get('item', []))
        
        print(f"Found {len(requests)} requests in collection")
        
        # Generate MCP tools
        print("\n=== MCP TOOLS ===")
        mcp_tools = []
        for req in requests:
            tool = generate_mcp_tool(req['request'])
            mcp_tools.append(tool)
            print(f"- {tool['name']}: {tool['description']}")
        
        # Generate client methods
        print("\n=== CLIENT METHODS ===")
        client_methods = []
        for req in requests:
            method = generate_client_method(req['request'])
            client_methods.append(method)
        
        # Write output files
        output_dir = Path("generated")
        output_dir.mkdir(exist_ok=True)
        
        # Write MCP tools
        with open(output_dir / "mcp_tools.json", 'w') as f:
            json.dump(mcp_tools, f, indent=2)
        
        # Write client methods
        with open(output_dir / "client_methods.py", 'w') as f:
            f.write("# Generated OHIP client methods\n")
            f.write("# Add these methods to your OHIPClient class\n\n")
            for method in client_methods:
                f.write(method)
                f.write("\n")
        
        print(f"\n✅ Conversion complete!")
        print(f"📁 Output files:")
        print(f"   - {output_dir / 'mcp_tools.json'} (MCP tool definitions)")
        print(f"   - {output_dir / 'client_methods.py'} (Client methods)")
        print(f"\n📝 Next steps:")
        print(f"   1. Review the generated files")
        print(f"   2. Update src/ohip_mcp/api_clients/ohip_client.py with the new methods")
        print(f"   3. Update src/ohip_mcp/mcp_server/server.py with the new tools")
        print(f"   4. Test the integration")
        
    except Exception as e:
        print(f"❌ Error converting collection: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
